"""
Collector Manager - manages all metric/log collectors.
Similar to Datadog's collector/check system.
"""

import asyncio
import logging
from typing import List
from agent.pkg.config.loader import AgentConfig
from agent.internal.core.component import Component
from agent.collectors.host_collector import HostMetricsCollector
from agent.collectors.container_collector import ContainerMetricsCollector
from agent.collectors.log_collector import LogCollector
from agent.collectors.network_collector import NetworkCollector
from agent.buffer import DataBuffer

logger = logging.getLogger(__name__)


class CollectorManager(Component):
    """
    Manages all collectors.
    
    Similar to Datadog's check manager:
    - Loads and runs collectors
    - Manages collector lifecycle
    - Handles collector errors
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__("collectors")
        self.config = config
        self.collectors: List = []
        self.collector_tasks: List[asyncio.Task] = []
        
        # Initialize buffer
        self.buffer = DataBuffer(
            max_size=config.buffer_size,
            flush_interval=config.flush_interval,
        )
        
        # Initialize collectors based on config
        self._initialize_collectors()
    
    def _initialize_collectors(self):
        """Initialize collectors based on configuration."""
        if self.config.collect_host_metrics:
            self.collectors.append(
                HostMetricsCollector(self.config, self.buffer)
            )
        
        if self.config.collect_container_metrics:
            self.collectors.append(
                ContainerMetricsCollector(self.config, self.buffer)
            )
        
        if self.config.collect_logs:
            self.collectors.append(
                LogCollector(self.config, self.buffer)
            )
        
        if self.config.collect_network:
            self.collectors.append(
                NetworkCollector(self.config, self.buffer)
            )
        
        logger.info(f"Initialized {len(self.collectors)} collectors")
    
    async def start(self):
        """Start all collectors."""
        for collector in self.collectors:
            task = asyncio.create_task(self._run_collector(collector))
            self.collector_tasks.append(task)
            logger.info(f"Started collector: {collector.__class__.__name__}")
    
    async def stop(self):
        """Stop all collectors."""
        # Cancel all tasks
        for task in self.collector_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.collector_tasks:
            await asyncio.gather(*self.collector_tasks, return_exceptions=True)
        
        # Stop collectors
        for collector in self.collectors:
            try:
                await collector.stop()
            except Exception as e:
                logger.error(f"Error stopping collector {collector.__class__.__name__}: {e}")
    
    async def _run_collector(self, collector):
        """Run a collector continuously."""
        while self.running:
            try:
                await collector.collect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Collector {collector.__class__.__name__} error: {e}")
            
            await asyncio.sleep(collector.interval)
    
    def get_status(self) -> dict:
        """Get collector manager status."""
        status = super().get_status()
        status.update({
            "collectors_count": len(self.collectors),
            "collectors": [
                {
                    "name": c.__class__.__name__,
                    "interval": getattr(c, 'interval', 0),
                }
                for c in self.collectors
            ],
        })
        return status
