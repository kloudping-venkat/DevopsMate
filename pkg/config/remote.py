"""
Remote configuration support.
Similar to Datadog's remote config system.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import aiohttp
import json

logger = logging.getLogger(__name__)


class RemoteConfigClient:
    """
    Client for fetching remote configuration.
    
    Similar to Datadog's remote config:
    - Polls for config updates
    - Version tracking
    - Change notifications
    - Hot-reload support
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        tenant_id: str,
        poll_interval: float = 60.0,
        on_config_update: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.poll_interval = poll_interval
        self.on_config_update = on_config_update
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._current_version: Optional[str] = None
        self._current_config: Optional[Dict[str, Any]] = None
    
    async def start(self):
        """Start remote config client."""
        self._running = True
        self._session = aiohttp.ClientSession(
            headers={
                "X-API-Key": self.api_key,
                "X-Tenant-ID": self.tenant_id,
                "User-Agent": "DevopsMate-Agent/1.0.0",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )
        
        # Initial fetch
        await self._fetch_config()
        
        # Start polling
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Remote config client started")
    
    async def stop(self):
        """Stop remote config client."""
        self._running = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        if self._session:
            await self._session.close()
        
        logger.info("Remote config client stopped")
    
    async def _poll_loop(self):
        """Poll for config updates."""
        while self._running:
            try:
                await self._fetch_config()
            except Exception as e:
                logger.error(f"Error fetching remote config: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    async def _fetch_config(self) -> Optional[Dict[str, Any]]:
        """Fetch configuration from remote endpoint."""
        url = f"{self.endpoint}/api/v1/agent/config"
        params = {}
        
        if self._current_version:
            params["version"] = self._current_version
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 304:
                    # Not modified
                    return self._current_config
                
                if response.status == 200:
                    config = await response.json()
                    new_version = config.get("version")
                    
                    # Check if config changed
                    if new_version != self._current_version:
                        self._current_version = new_version
                        self._current_config = config.get("config", {})
                        
                        # Notify of update
                        if self.on_config_update:
                            try:
                                self.on_config_update(self._current_config)
                            except Exception as e:
                                logger.error(f"Error in config update callback: {e}")
                        
                        logger.info(f"Remote config updated to version {new_version}")
                    
                    return self._current_config
                
                else:
                    logger.warning(f"Failed to fetch remote config: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching remote config: {e}")
            return None
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get current remote configuration."""
        return self._current_config
