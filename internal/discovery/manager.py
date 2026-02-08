"""
Discovery Manager - manages all discovery modules.
Similar to Datadog's discovery system.
"""

import asyncio
import logging
from agent.pkg.config.loader import AgentConfig
from agent.internal.core.component import Component
from agent.discovery.process_discovery import ProcessDiscovery
from agent.discovery.container_discovery import ContainerDiscovery
from agent.discovery.network_discovery import NetworkDiscovery

logger = logging.getLogger(__name__)


class DiscoveryManager(Component):
    """
    Manages discovery of processes, containers, and network.
    
    Similar to Datadog's autodiscovery:
    - Process discovery
    - Container discovery
    - Network discovery
    - Periodic refresh
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__("discovery")
        self.config = config
        
        # Discovery modules
        self.process_discovery = ProcessDiscovery(config)
        self.container_discovery = ContainerDiscovery(config)
        self.network_discovery = NetworkDiscovery(config)
        
        self._discovery_task: asyncio.Task = None
    
    async def start(self):
        """Start discovery manager."""
        # Run initial discovery
        await self._run_discovery()
        
        # Start periodic discovery
        self._discovery_task = asyncio.create_task(self._periodic_discovery())
        logger.info("Discovery manager started")
    
    async def stop(self):
        """Stop discovery manager."""
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        logger.info("Discovery manager stopped")
    
    async def _run_discovery(self):
        """Run discovery for all modules."""
        try:
            # Discover processes
            processes = await self.process_discovery.discover()
            logger.debug(f"Discovered {len(processes)} processes")
            
            # Discover containers
            containers = await self.container_discovery.discover()
            logger.debug(f"Discovered {len(containers)} containers")
            
            # Discover network
            connections = await self.network_discovery.discover()
            logger.debug(f"Discovered {len(connections)} network connections")
            
        except Exception as e:
            logger.error(f"Discovery error: {e}")
    
    async def _periodic_discovery(self):
        """Run discovery periodically."""
        while self.running:
            await asyncio.sleep(self.config.discovery_interval)
            if self.running:
                await self._run_discovery()
    
    def get_status(self) -> dict:
        """Get discovery manager status."""
        status = super().get_status()
        status.update({
            "discovery_interval": self.config.discovery_interval,
        })
        return status
