"""
Core Agent class - main agent implementation.
Similar to Datadog's internal/core/agent structure.
"""

import asyncio
import logging
from typing import List, Dict, Any

from agent.pkg.config.loader import AgentConfig
from agent.internal.core.component import Component, ComponentManager
from agent.internal.core.collector_manager import CollectorManager
from agent.internal.core.forwarder import Forwarder
from agent.internal.discovery.manager import DiscoveryManager

logger = logging.getLogger(__name__)


class Agent:
    """
    Main Agent class.
    
    Similar to Datadog's Agent structure:
    - Component-based architecture
    - Lifecycle management
    - Health monitoring
    - Status reporting
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.running = False
        
        # Component manager (like Datadog's component system)
        self.component_manager = ComponentManager()
        
        # Discovery manager
        self.discovery_manager = DiscoveryManager(config)
        self.component_manager.register("discovery", self.discovery_manager)
        
        # Collector manager
        self.collector_manager = CollectorManager(config)
        self.component_manager.register("collectors", self.collector_manager)
        
        # Forwarder (data export)
        self.forwarder = Forwarder(config)
        self.component_manager.register("forwarder", self.forwarder)
        
        # Stats
        self.stats = {
            "metrics_collected": 0,
            "logs_collected": 0,
            "traces_collected": 0,
            "bytes_sent": 0,
            "errors": 0,
            "uptime_seconds": 0,
        }
    
    async def start(self):
        """Start the agent and all components."""
        logger.info("Starting DevopsMate Agent")
        logger.info(f"Endpoint: {self.config.endpoint}")
        logger.info(f"Tenant: {self.config.tenant_id}")
        
        self.running = True
        
        # Start all components
        await self.component_manager.start_all()
        
        logger.info("Agent started successfully")
    
    async def stop(self):
        """Stop the agent gracefully."""
        logger.info("Stopping agent...")
        self.running = False
        
        # Stop all components
        await self.component_manager.stop_all()
        
        logger.info("Agent stopped")
        self._print_stats()
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status (similar to Datadog's status command)."""
        return {
            "running": self.running,
            "stats": self.stats,
            "components": self.component_manager.get_status(),
        }
    
    def _print_stats(self):
        """Print agent statistics."""
        logger.info("=== Agent Statistics ===")
        for key, value in self.stats.items():
            logger.info(f"  {key}: {value}")
