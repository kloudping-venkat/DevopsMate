"""Data exporter for sending collected data to the platform."""

import asyncio
import gzip
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from agent.buffer import DataBuffer, BufferedData

logger = logging.getLogger(__name__)


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
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.buffer = buffer
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        
        self._stats = {
            "bytes_sent": 0,
            "requests_made": 0,
            "requests_failed": 0,
            "items_sent": 0,
        }
    
    async def start(self):
        """Start the exporter."""
        self._running = True
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
        
        # Recover any spilled data
        await self.buffer.recover_from_disk()
        
        # Start flush loop
        while self._running:
            try:
                await self._flush_all()
            except Exception as e:
                logger.error(f"Flush error: {e}")
            
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
    
    async def _send_with_retry(
        self,
        data_type: str,
        payloads: List[Dict[str, Any]],
    ) -> bool:
        """Send data with exponential backoff retry."""
        endpoint_map = {
            "metrics": f"{self.endpoint}/metrics",
            "logs": f"{self.endpoint}/logs",
            "traces": f"{self.endpoint}/traces",
            "topology": f"{self.endpoint}/topology",
        }
        
        url = endpoint_map.get(data_type, f"{self.endpoint}/{data_type}")
        
        for attempt in range(self.max_retries):
            try:
                # Compress payload
                payload_json = json.dumps(payloads)
                compressed = gzip.compress(payload_json.encode())
                
                async with self._session.post(url, data=compressed) as response:
                    self._stats["requests_made"] += 1
                    
                    if response.status == 200:
                        self._stats["bytes_sent"] += len(compressed)
                        self._stats["items_sent"] += len(payloads)
                        logger.debug(f"Sent {len(payloads)} {data_type} items")
                        return True
                    
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                    
                    elif response.status >= 500:
                        # Server error, retry with backoff
                        logger.warning(f"Server error {response.status}, retrying...")
                        await asyncio.sleep(2 ** attempt)
                    
                    else:
                        # Client error, don't retry
                        logger.error(f"Client error {response.status}: {await response.text()}")
                        self._stats["requests_failed"] += 1
                        return False
                        
            except aiohttp.ClientError as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(2 ** attempt)
        
        self._stats["requests_failed"] += 1
        return False
    
    async def send_topology(self, topology: Dict[str, Any]) -> bool:
        """Send topology data immediately."""
        return await self._send_with_retry("topology", [topology])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get exporter statistics."""
        return self._stats.copy()
