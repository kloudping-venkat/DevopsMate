"""Data exporter for sending collected data to the platform."""

import asyncio
import gzip
import json
import logging
import socket
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

from agent.buffer import DataBuffer, BufferedData

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, don't try
    HALF_OPEN = "half_open"  # Testing if recovered


class DataExporter:
    """
    Exports collected data to the DevopsMate platform.
    
    Features:
    - Batched exports for efficiency
    - Compression (gzip)
    - Automatic retry with exponential backoff
    - Connection pooling
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        tenant_id: str,
        buffer: DataBuffer,
        batch_size: int = 1000,
        flush_interval: float = 10.0,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 300.0,  # 5 minutes
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.buffer = buffer
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        
        # Circuit breaker state
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._circuit_open_until: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        self._dns_failures = 0
        
        # Extract hostname for DNS checks
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.endpoint)
            self._hostname = parsed.hostname
        except Exception:
            self._hostname = None
        
        self._stats = {
            "bytes_sent": 0,
            "requests_made": 0,
            "requests_failed": 0,
            "items_sent": 0,
            "circuit_breaker_opens": 0,
            "dns_failures": 0,
        }
    
    async def start(self):
        """Start the exporter."""
        self._running = True
        
        # Check DNS before starting
        if not await self._check_dns():
            logger.error("DNS resolution failed, cannot start exporter")
            # Wait and retry DNS check
            await asyncio.sleep(60)
            if not await self._check_dns():
                logger.error("DNS resolution still failing after retry")
                # Continue anyway, circuit breaker will handle it
        
        self._session = aiohttp.ClientSession(
            headers={
                "X-API-Key": self.api_key,
                "X-Tenant-ID": self.tenant_id,
                "Content-Type": "application/json",
                "Content-Encoding": "gzip",
                "User-Agent": "DevopsMate-Agent/0.1.0",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )
        
        # Recover any spilled data (limited batch to avoid memory spike)
        await self.buffer.recover_from_disk(max_files=10)
        
        # Start flush loop
        while self._running:
            try:
                await self._flush_all()
            except Exception as e:
                logger.error(f"Flush error: {e}", exc_info=True)
                # Don't let one error stop the exporter
                await asyncio.sleep(self.flush_interval)
            
            await asyncio.sleep(self.flush_interval)
    
    async def stop(self):
        """Stop the exporter."""
        self._running = False
        await self.flush()
        
        if self._session:
            await self._session.close()
    
    async def flush(self):
        """Flush all buffers immediately."""
        await self._flush_all()
    
    async def _flush_all(self):
        """Flush all data types."""
        # Check circuit breaker
        if self._circuit_state == CircuitState.OPEN:
            if self._circuit_open_until and datetime.utcnow() < self._circuit_open_until:
                logger.debug("Circuit breaker open, skipping flush")
                return
            else:
                # Try to close circuit (half-open state)
                logger.info("Attempting to close circuit breaker (half-open)")
                self._circuit_state = CircuitState.HALF_OPEN
                self._failure_count = 0
        
        # Recover spilled data in small batches (LIFO - newest first)
        # Only recover if circuit is not open or in half-open state
        if self._circuit_state != CircuitState.OPEN:
            recovered = await self.buffer.recover_from_disk(max_files=5)
            if recovered > 0:
                logger.info(f"Recovered {recovered} items from disk, attempting to send...")
        
        # Then flush current in-memory buffers
        for data_type in ["metrics", "logs", "traces"]:
            await self._flush_type(data_type)
    
    async def _flush_type(self, data_type: str):
        """Flush a specific data type."""
        batch = await self.buffer.get_batch(data_type, self.batch_size)
        if not batch:
            return
        
        # Prepare payload
        payloads = [item.payload for item in batch]
        
        # Send with retry
        success = await self._send_with_retry(data_type, payloads)
        
        if not success:
            # Return failed items to buffer
            await self.buffer.return_failed(batch)
    
    async def _check_dns(self) -> bool:
        """Check if DNS resolution works for the endpoint."""
        if not self._hostname:
            return True  # Can't check, assume OK
        
        try:
            socket.gethostbyname(self._hostname)
            self._dns_failures = 0
            return True
        except socket.gaierror as e:
            self._dns_failures += 1
            self._stats["dns_failures"] += 1
            logger.error(f"DNS resolution failure ({self._dns_failures}): {e}")
            
            # Open circuit after 5 consecutive DNS failures
            if self._dns_failures >= self.circuit_breaker_threshold:
                self._open_circuit("DNS resolution failures")
            
            return False
        except Exception as e:
            logger.warning(f"DNS check error: {e}")
            return True  # Assume OK for other errors
    
    def _open_circuit(self, reason: str):
        """Open the circuit breaker."""
        if self._circuit_state != CircuitState.OPEN:
            self._circuit_state = CircuitState.OPEN
            self._circuit_open_until = datetime.utcnow() + timedelta(seconds=self.circuit_breaker_timeout)
            self._stats["circuit_breaker_opens"] += 1
            logger.warning(
                f"Circuit breaker opened due to: {reason}. "
                f"Will retry in {self.circuit_breaker_timeout}s"
            )
    
    def _record_success(self):
        """Record a successful request."""
        self._failure_count = 0
        self._dns_failures = 0
        self._last_success_time = datetime.utcnow()
        
        if self._circuit_state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker closed after successful request")
            self._circuit_state = CircuitState.CLOSED
        elif self._circuit_state == CircuitState.OPEN:
            # Shouldn't happen, but handle it
            self._circuit_state = CircuitState.CLOSED
    
    def _record_failure(self, error: Exception):
        """Record a failed request."""
        self._failure_count += 1
        
        # Check if we should open circuit breaker
        if self._failure_count >= self.circuit_breaker_threshold:
            error_msg = str(error)
            if "name resolution" in error_msg.lower() or "dns" in error_msg.lower():
                self._dns_failures += 1
                self._stats["dns_failures"] += 1
                if self._dns_failures >= self.circuit_breaker_threshold:
                    self._open_circuit("DNS resolution failures")
            else:
                self._open_circuit(f"Connection failures ({self._failure_count})")
    
    async def _send_with_retry(
        self,
        data_type: str,
        payloads: List[Dict[str, Any]],
    ) -> bool:
        """Send data with exponential backoff retry."""
        # Check if session is initialized
        if not self._session:
            logger.warning(f"Session not initialized, skipping {data_type} export")
            return False
        
        endpoint_map = {
            "metrics": f"{self.endpoint}/metrics",
            "logs": f"{self.endpoint}/logs",
            "traces": f"{self.endpoint}/traces",
            "topology": f"{self.endpoint.replace('/api/v1/ingest', '/api/v2/topology')}/ingest",
        }
        
        url = endpoint_map.get(data_type, f"{self.endpoint}/{data_type}")
        
        # Format payload according to API schema
        if data_type == "metrics":
            request_body = {"metrics": payloads}
        elif data_type == "logs":
            request_body = {"logs": payloads}
        elif data_type == "traces":
            # Traces endpoint expects array directly
            request_body = payloads
        else:
            request_body = payloads
        
        for attempt in range(self.max_retries):
            try:
                # Compress payload
                payload_json = json.dumps(request_body)
                compressed = gzip.compress(payload_json.encode())
                
                async with self._session.post(url, data=compressed) as response:
                    self._stats["requests_made"] += 1
                    
                    if response.status == 200:
                        self._stats["bytes_sent"] += len(compressed)
                        self._stats["items_sent"] += len(payloads)
                        self._record_success()
                        logger.debug(f"Sent {len(payloads)} {data_type} items")
                        return True
                    
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue  # Don't count as failure
                    
                    elif response.status >= 500:
                        # Server error, retry with exponential backoff
                        delay = min(
                            self.initial_retry_delay * (2 ** attempt),
                            self.max_retry_delay
                        )
                        logger.warning(
                            f"Server error {response.status}, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue  # Retry
                    
                    else:
                        # Client error, don't retry
                        response_text = await response.text()
                        logger.error(
                            f"Client error {response.status} for {data_type}: {response_text[:500]}"
                        )
                        self._stats["requests_failed"] += 1
                        return False
                        
            except aiohttp.ClientConnectorError as e:
                error_msg = str(e).lower()
                if "name resolution" in error_msg or "dns" in error_msg:
                    self._dns_failures += 1
                    self._stats["dns_failures"] += 1
                    logger.error(f"DNS resolution failure ({self._dns_failures}): {e}")
                    
                    if self._dns_failures >= self.circuit_breaker_threshold:
                        self._open_circuit("DNS resolution failures")
                        return False
                else:
                    logger.error(f"Connection error: {e}")
                
                self._record_failure(e)
                delay = min(
                    self.initial_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                await asyncio.sleep(delay)
            
            except aiohttp.ClientError as e:
                logger.error(f"HTTP client error: {e}")
                self._record_failure(e)
                delay = min(
                    self.initial_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                await asyncio.sleep(delay)
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self._record_failure(e)
                delay = min(
                    self.initial_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                await asyncio.sleep(delay)
        
        self._stats["requests_failed"] += 1
        return False
    
    async def send_topology(self, topology: Dict[str, Any]) -> bool:
        """Send topology data immediately."""
        return await self._send_with_retry("topology", [topology])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get exporter statistics."""
        stats = self._stats.copy()
        stats.update({
            "circuit_state": self._circuit_state.value,
            "failure_count": self._failure_count,
            "dns_failures": self._dns_failures,
            "circuit_open_until": self._circuit_open_until.isoformat() if self._circuit_open_until else None,
        })
        return stats
