"""
DevopsMate Universal Agent - Main Entry Point

The Universal Agent combines:
- Dynatrace OneAgent capabilities (auto-discovery, auto-instrumentation)
- OpenTelemetry Collector (standard protocols, flexibility)

Usage:
    python -m agent.agent --config agent.yaml
    
Or as a service:
    devopsmate-agent start
"""

import asyncio
import signal
import sys
import argparse
from pathlib import Path
from typing import Optional
import logging

import yaml

from agent.config import AgentConfig
from agent.discovery.process_discovery import ProcessDiscovery
from agent.discovery.container_discovery import ContainerDiscovery
from agent.discovery.network_discovery import NetworkDiscovery
from agent.collectors.host_collector import HostMetricsCollector
from agent.collectors.container_collector import ContainerMetricsCollector
from agent.collectors.log_collector import LogCollector
from agent.collectors.network_collector import NetworkCollector
from agent.instrumentation.auto_instrumentor import AutoInstrumentor
from agent.exporter import DataExporter
from agent.buffer import DataBuffer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UniversalAgent:
    """
    DevopsMate Universal Agent
    
    Features:
    - Auto-discovery of processes, containers, services
    - Auto-instrumentation for supported languages
    - Metric, log, and trace collection
    - Local buffering (survives network issues)
    - Efficient compression and batching
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.running = False
        
        # Initialize components
        # Determine installation directory for buffer spilling (user-writable)
        import os
        install_dir = os.getenv("DEVOPSMATE_AGENT_DIR", os.getcwd())
        buffer_spill_path = os.path.join(install_dir, "buffer")
        
        self.buffer = DataBuffer(
            max_size=config.buffer_size,
            flush_interval=config.flush_interval,
            spill_path=buffer_spill_path,
        )
        
        self.exporter = DataExporter(
            endpoint=config.endpoint,
            api_key=config.api_key,
            tenant_id=config.tenant_id,
            buffer=self.buffer,
        )
        
        # Discovery modules
        self.process_discovery = ProcessDiscovery(config)
        self.container_discovery = ContainerDiscovery(config)
        self.network_discovery = NetworkDiscovery(config)
        
        # Collectors
        self.collectors = []
        
        if config.collect_host_metrics:
            self.collectors.append(HostMetricsCollector(config, self.buffer))
        
        if config.collect_container_metrics:
            self.collectors.append(ContainerMetricsCollector(config, self.buffer))
        
        if config.collect_logs:
            self.collectors.append(LogCollector(config, self.buffer))
        
        if config.collect_network:
            self.collectors.append(NetworkCollector(config, self.buffer))
        
        # Auto-instrumentation
        self.instrumentor = AutoInstrumentor(config) if config.auto_instrument else None
        
        # Stats
        self.stats = {
            "metrics_collected": 0,
            "logs_collected": 0,
            "traces_collected": 0,
            "bytes_sent": 0,
            "errors": 0,
        }
    
    async def start(self):
        """Start the agent."""
        logger.info(f"Starting DevopsMate Agent v{__import__('agent').__version__}")
        logger.info(f"Endpoint: {self.config.endpoint}")
        logger.info(f"Tenant: {self.config.tenant_id}")
        
        self.running = True
        
        # Start discovery
        await self._run_discovery()
        
        # Start auto-instrumentation if enabled
        if self.instrumentor:
            await self.instrumentor.start()
        
        # Start collectors
        collector_tasks = []
        for collector in self.collectors:
            task = asyncio.create_task(self._run_collector(collector))
            collector_tasks.append(task)
        
        # Start exporter
        exporter_task = asyncio.create_task(self.exporter.start())
        
        # Start periodic discovery
        discovery_task = asyncio.create_task(self._periodic_discovery())
        
        # Wait for shutdown
        try:
            await asyncio.gather(
                *collector_tasks,
                exporter_task,
                discovery_task,
            )
        except asyncio.CancelledError:
            logger.info("Agent shutting down...")
    
    async def stop(self):
        """Stop the agent gracefully."""
        logger.info("Stopping agent...")
        self.running = False
        
        # Stop collectors
        for collector in self.collectors:
            await collector.stop()
        
        # Flush remaining data
        await self.exporter.flush()
        await self.exporter.stop()
        
        # Stop instrumentor
        if self.instrumentor:
            await self.instrumentor.stop()
        
        logger.info("Agent stopped")
        self._print_stats()
    
    async def _run_discovery(self):
        """Run initial discovery."""
        logger.info("Running initial discovery...")
        
        # Discover processes
        processes = await self.process_discovery.discover()
        logger.info(f"Discovered {len(processes)} processes")
        
        # Discover containers
        containers = await self.container_discovery.discover()
        logger.info(f"Discovered {len(containers)} containers")
        
        # Discover network connections
        connections = await self.network_discovery.discover()
        logger.info(f"Discovered {len(connections)} network connections")
        
        # Send topology data
        await self.exporter.send_topology({
            "processes": processes,
            "containers": containers,
            "connections": connections,
        })
    
    async def _periodic_discovery(self):
        """Run discovery periodically."""
        while self.running:
            await asyncio.sleep(self.config.discovery_interval)
            if self.running:
                await self._run_discovery()
    
    async def _run_collector(self, collector):
        """Run a collector continuously."""
        logger.info(f"Starting collector: {collector.__class__.__name__}")
        
        while self.running:
            try:
                await collector.collect()
                self.stats["metrics_collected"] += collector.last_count
            except PermissionError as e:
                # Permission errors are expected and handled gracefully by collectors
                # Log as debug to avoid noise in error logs
                logger.debug(f"Collector permission issue (expected): {e}")
            except Exception as e:
                # Check if it's a permission-related error
                error_str = str(e).lower()
                if "permission denied" in error_str or "errno 13" in error_str:
                    logger.debug(f"Collector permission issue (expected): {e}")
                else:
                    logger.error(f"Collector error: {e}")
                    self.stats["errors"] += 1
            
            await asyncio.sleep(collector.interval)
    
    def _print_stats(self):
        """Print agent statistics."""
        logger.info("=== Agent Statistics ===")
        for key, value in self.stats.items():
            logger.info(f"  {key}: {value}")


def load_config(config_path: Optional[str] = None) -> AgentConfig:
    """Load configuration from file or environment."""
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
            return AgentConfig(**config_data)
    
    # Load from environment
    return AgentConfig.from_env()


def main():
    parser = argparse.ArgumentParser(description="DevopsMate Universal Agent")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--endpoint", "-e", help="API endpoint")
    parser.add_argument("--api-key", "-k", help="API key")
    parser.add_argument("--tenant-id", "-t", help="Tenant ID")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load config
    config = load_config(args.config)
    
    # Override with CLI args
    if args.endpoint:
        config.endpoint = args.endpoint
    if args.api_key:
        config.api_key = args.api_key
    if args.tenant_id:
        config.tenant_id = args.tenant_id
    
    # Create agent
    agent = UniversalAgent(config)
    
    # Setup signal handlers
    loop = asyncio.new_event_loop()
    
    def shutdown_handler():
        loop.create_task(agent.stop())
    
    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGTERM, shutdown_handler)
        loop.add_signal_handler(signal.SIGINT, shutdown_handler)
    
    # Run agent
    try:
        loop.run_until_complete(agent.start())
    except KeyboardInterrupt:
        loop.run_until_complete(agent.stop())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
