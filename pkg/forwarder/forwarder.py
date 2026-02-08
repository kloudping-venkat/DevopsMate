"""
Enhanced forwarder with multiple endpoints and better retry strategies.
Similar to Datadog's forwarder implementation.
"""

import asyncio
import gzip
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

import aiohttp
from aiohttp import ClientConnectorError, ClientTimeout

from agent.buffer import DataBuffer
from agent.pkg.forwarder.retry import RetryStrategy, ExponentialBackoffWithJitter

logger = logging.getLogger(__name__)


@dataclass
class EndpointConfig:
    """Configuration for a single endpoint."""
    url: str
    api_key: str
    timeout: float = 30.0
    max_connections: int = 10
    enabled: bool = True


@dataclass
class ForwarderConfig:
    """Forwarder configuration."""
    endpoints: List[EndpointConfig] = field(default_factory=list)
    batch_size: int = 1000
    flush_interval: float = 10.0
    retry_strategy: Optional[RetryStrategy] = None
    compression: bool = True
    connection_pool_size: int = 10
    max_connections_per_host: int = 10


class Forwarder:
    """
    Enhanced forwarder with multiple endpoints and advanced retry strategies.
    
    Similar to Datadog's forwarder:
    - Multiple endpoint support (primary + failover)
    - Exponential backoff with jitter
    - Connection pooling
    - Event platform support
    - Better error handling
    """
    
    def __init__(
        self,
        config: ForwarderConfig,
        buffer: DataBuffer,
    ):
        self.config = config
        self.buffer = buffer
        
        # Use default retry strategy if not provided
        if not config.retry_strategy:
            config.retry_strategy = ExponentialBackoffWithJitter(
                max_retries=3,
                base_delay=1.0,
                max_delay=60.0,
            )
        
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        
        # Stats
        self._stats = {
            "bytes_sent": 0,
            "requests_made": 0,
            "requests_failed": 0,
            "items_sent": 0,
            "endpoint_stats": {},
        }
    
    async def start(self):
        """Start the forwarder."""
        self._running = True
        
        # Create sessions for each endpoint
        for endpoint in self.config.endpoints:
            if endpoint.enabled:
                await self._create_session(endpoint)
        
        # Recover any spilled data
        await self.buffer.recover_from_disk()
        
        # Start flush loop
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info(f"Forwarder started with {len(self._sessions)} endpoints")
    
    async def stop(self):
        """Stop the forwarder."""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining data
        await self.flush()
        
        # Close all sessions
        for session in self._sessions.values():
            await session.close()
        
        self._sessions.clear()
        logger.info("Forwarder stopped")
    
    async def _create_session(self, endpoint: EndpointConfig):
        """Create a session for an endpoint."""
        connector = aiohttp.TCPConnector(
            limit=self.config.connection_pool_size,
            limit_per_host=endpoint.max_connections,
        )
        
        timeout = ClientTimeout(total=endpoint.timeout)
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "X-API-Key": endpoint.api_key,
                "Content-Type": "application/json",
                "Content-Encoding": "gzip" if self.config.compression else "identity",
                "User-Agent": "DevopsMate-Agent/1.0.0",
            },
        )
        
        self._sessions[endpoint.url] = session
        self._stats["endpoint_stats"][endpoint.url] = {
            "requests_made": 0,
            "requests_failed": 0,
            "bytes_sent": 0,
        }
    
    async def _flush_loop(self):
        """Main flush loop."""
        while self._running:
            try:
                await self._flush_all()
            except Exception as e:
                logger.error(f"Flush loop error: {e}")
            
            await asyncio.sleep(self.config.flush_interval)
    
    async def flush(self):
        """Flush all buffers immediately."""
        await self._flush_all()
    
    async def _flush_all(self):
        """Flush all data types."""
        for data_type in ["metrics", "logs", "traces", "events"]:
            await self._flush_type(data_type)
    
    async def _flush_type(self, data_type: str):
        """Flush a specific data type."""
        batch = await self.buffer.get_batch(data_type, self.config.batch_size)
        if not batch:
            return
        
        # Prepare payload
        payloads = [item.payload for item in batch]
        
        # Send with retry to all endpoints
        success = await self._send_with_retry(data_type, payloads)
        
        if not success:
            # Return failed items to buffer
            await self.buffer.return_failed(batch)
    
    async def _send_with_retry(
        self,
        data_type: str,
        payloads: List[Dict[str, Any]],
    ) -> bool:
        """Send data with retry to multiple endpoints."""
        # Try each endpoint in order
        for endpoint in self.config.endpoints:
            if not endpoint.enabled:
                continue
            
            url = self._get_url_for_type(endpoint.url, data_type)
            session = self._sessions.get(endpoint.url)
            
            if not session:
                continue
            
            # Try with retry strategy
            success = await self._send_to_endpoint(
                session=session,
                url=url,
                endpoint_url=endpoint.url,
                data_type=data_type,
                payloads=payloads,
            )
            
            if success:
                return True
        
        # All endpoints failed
        return False
    
    async def _send_to_endpoint(
        self,
        session: aiohttp.ClientSession,
        url: str,
        endpoint_url: str,
        data_type: str,
        payloads: List[Dict[str, Any]],
    ) -> bool:
        """Send data to a specific endpoint with retry."""
        attempt = 0
        
        while True:
            try:
                # Prepare payload
                if self.config.compression:
                    payload_json = json.dumps(payloads)
                    data = gzip.compress(payload_json.encode())
                else:
                    data = json.dumps(payloads).encode()
                
                # Send request
                async with session.post(url, data=data) as response:
                    self._stats["requests_made"] += 1
                    self._stats["endpoint_stats"][endpoint_url]["requests_made"] += 1
                    
                    status_code = response.status
                    
                    if status_code == 200:
                        # Success
                        self._stats["bytes_sent"] += len(data)
                        self._stats["items_sent"] += len(payloads)
                        self._stats["endpoint_stats"][endpoint_url]["bytes_sent"] += len(data)
                        logger.debug(f"Sent {len(payloads)} {data_type} items to {endpoint_url}")
                        return True
                    
                    # Check if we should retry
                    should_retry = await self.config.retry_strategy.should_retry(
                        attempt=attempt,
                        status_code=status_code,
                    )
                    
                    if not should_retry:
                        # Don't retry
                        error_text = await response.text()
                        logger.error(f"Client error {status_code} from {endpoint_url}: {error_text}")
                        self._stats["requests_failed"] += 1
                        self._stats["endpoint_stats"][endpoint_url]["requests_failed"] += 1
                        return False
                    
                    # Get delay and wait
                    delay = await self.config.retry_strategy.get_delay(attempt)
                    
                    # Handle rate limiting
                    if status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", delay))
                        delay = max(delay, retry_after)
                        logger.warning(f"Rate limited by {endpoint_url}, waiting {delay:.1f}s")
                    else:
                        logger.warning(f"Server error {status_code} from {endpoint_url}, retrying in {delay:.1f}s")
                    
                    await asyncio.sleep(delay)
                    attempt += 1
                    
            except (ClientConnectorError, TimeoutError) as e:
                # Connection error
                should_retry = await self.config.retry_strategy.should_retry(
                    attempt=attempt,
                    error=e,
                )
                
                if not should_retry:
                    logger.error(f"Connection error to {endpoint_url}: {e}")
                    self._stats["requests_failed"] += 1
                    self._stats["endpoint_stats"][endpoint_url]["requests_failed"] += 1
                    return False
                
                delay = await self.config.retry_strategy.get_delay(attempt)
                logger.warning(f"Connection error to {endpoint_url}, retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
                attempt += 1
                
            except Exception as e:
                logger.error(f"Unexpected error sending to {endpoint_url}: {e}")
                self._stats["requests_failed"] += 1
                self._stats["endpoint_stats"][endpoint_url]["requests_failed"] += 1
                return False
    
    def _get_url_for_type(self, base_url: str, data_type: str) -> str:
        """Get URL for a specific data type."""
        endpoint_map = {
            "metrics": f"{base_url}/api/v1/ingest/metrics",
            "logs": f"{base_url}/api/v1/ingest/logs",
            "traces": f"{base_url}/api/v1/ingest/traces",
            "events": f"{base_url}/api/v1/ingest/events",
            "topology": f"{base_url}/api/v1/ingest/topology",
        }
        return endpoint_map.get(data_type, f"{base_url}/api/v1/ingest/{data_type}")
    
    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send an event immediately (event platform support)."""
        return await self._send_with_retry("events", [event])
    
    async def send_topology(self, topology: Dict[str, Any]) -> bool:
        """Send topology data immediately."""
        return await self._send_with_retry("topology", [topology])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get forwarder statistics."""
        return {
            **self._stats,
            "endpoints_count": len(self._sessions),
            "running": self._running,
        }
