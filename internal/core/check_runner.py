"""
Check runner - runs individual checks/collectors.
Similar to Datadog's check runner.
"""

import asyncio
from typing import List, Dict, Any, Optional
from agent.pkg.config.loader import AgentConfig
from agent.collectors.host_collector import HostMetricsCollector
from agent.collectors.container_collector import ContainerMetricsCollector
from agent.collectors.log_collector import LogCollector
from agent.collectors.network_collector import NetworkCollector
from agent.buffer import DataBuffer


class CheckRunner:
    """
    Runs individual checks/collectors.
    """
    
    # Registry of available checks
    _check_registry = {
        'host_metrics': HostMetricsCollector,
        'container_metrics': ContainerMetricsCollector,
        'log_collector': LogCollector,
        'network_collector': NetworkCollector,
    }
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config
        self.buffer = DataBuffer(max_size=1000, flush_interval=10) if config else None
    
    def list_checks(self) -> List[str]:
        """List all available checks."""
        return list(self._check_registry.keys())
    
    def run_check(self, check_name: str, instance: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a specific check.
        
        Args:
            check_name: Name of the check to run
            instance: Optional instance name
            
        Returns:
            Dict with check results
        """
        if check_name not in self._check_registry:
            raise ValueError(f"Unknown check: {check_name}. Available: {self.list_checks()}")
        
        check_class = self._check_registry[check_name]
        
        if not self.config:
            from agent.config import AgentConfig
            self.config = AgentConfig()
            self.buffer = DataBuffer(max_size=1000, flush_interval=10)
        
        # Create check instance
        check = check_class(self.config, self.buffer)
        
        # Run check
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(check.collect())
            
            return {
                'status': 'ok',
                'check_name': check_name,
                'instance': instance,
                'metrics': getattr(check, 'last_metrics', []),
                'errors': [],
            }
        except Exception as e:
            return {
                'status': 'error',
                'check_name': check_name,
                'instance': instance,
                'metrics': [],
                'errors': [str(e)],
            }
        finally:
            loop.close()
