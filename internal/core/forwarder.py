"""
Forwarder - forwards data to backend.
Similar to Datadog's forwarder component.
"""

import asyncio
import logging
from agent.pkg.config.loader import AgentConfig
from agent.internal.core.component import Component
from agent.pkg.forwarder.forwarder import Forwarder as EnhancedForwarder, ForwarderConfig, EndpointConfig
from agent.pkg.forwarder.retry import ExponentialBackoffWithJitter
from agent.buffer import DataBuffer

logger = logging.getLogger(__name__)


class Forwarder(Component):
    """
    Forwards collected data to DevopsMate backend.
    
    Similar to Datadog's forwarder:
    - Handles data export
    - Manages retries with exponential backoff + jitter
    - Compresses data
    - Batches requests
    - Multiple endpoint support (primary + failover)
    - Event platform support
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__("forwarder")
        self.config = config
        self.forwarder: EnhancedForwarder = None
        self.buffer: DataBuffer = None
    
    async def start(self):
        """Start the forwarder."""
        # Get buffer from collector manager (shared)
        # For now, create our own
        self.buffer = DataBuffer(
            max_size=self.config.buffer_size,
            flush_interval=self.config.flush_interval,
        )
        
        # Build endpoint configs
        endpoints = [
            EndpointConfig(
                url=self.config.endpoint,
                api_key=self.config.api_key,
                timeout=30.0,
                enabled=True,
            )
        ]
        
        # Add failover endpoints if configured
        if hasattr(self.config, 'failover_endpoints') and self.config.failover_endpoints:
            for failover in self.config.failover_endpoints:
                endpoints.append(EndpointConfig(
                    url=failover.get('url', ''),
                    api_key=failover.get('api_key', self.config.api_key),
                    timeout=failover.get('timeout', 30.0),
                    enabled=True,
                ))
        
        # Create forwarder config
        forwarder_config = ForwarderConfig(
            endpoints=endpoints,
            batch_size=self.config.max_batch_size,
            flush_interval=self.config.flush_interval,
            retry_strategy=ExponentialBackoffWithJitter(
                max_retries=3,
                base_delay=1.0,
                max_delay=60.0,
                jitter_factor=0.1,
            ),
            compression=True,
            connection_pool_size=10,
        )
        
        # Create enhanced forwarder
        self.forwarder = EnhancedForwarder(
            config=forwarder_config,
            buffer=self.buffer,
        )
        
        await self.forwarder.start()
        logger.info("Forwarder started")
    
    async def stop(self):
        """Stop the forwarder."""
        if self.forwarder:
            await self.forwarder.stop()
        
        logger.info("Forwarder stopped")
    
    def get_status(self) -> dict:
        """Get forwarder status."""
        status = super().get_status()
        if self.forwarder:
            stats = self.forwarder.get_stats()
            status.update({
                "endpoints": len(stats.get("endpoint_stats", {})),
                "bytes_sent": stats.get("bytes_sent", 0),
                "requests_made": stats.get("requests_made", 0),
                "requests_failed": stats.get("requests_failed", 0),
                "items_sent": stats.get("items_sent", 0),
            })
        return status
