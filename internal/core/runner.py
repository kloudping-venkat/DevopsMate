"""
Agent runner - manages agent lifecycle.
Similar to Datadog's agent runner.
"""

import asyncio
import logging
from agent.pkg.config.loader import AgentConfig
from agent.internal.core.agent import Agent

logger = logging.getLogger(__name__)


class AgentRunner:
    """
    Runs the agent and manages its lifecycle.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent = Agent(config)
        self._start_time = None
    
    async def start(self):
        """Start the agent."""
        import time
        self._start_time = time.time()
        await self.agent.start()
    
    async def stop(self):
        """Stop the agent."""
        await self.agent.stop()
    
    def get_uptime(self) -> float:
        """Get agent uptime in seconds."""
        if self._start_time:
            import time
            return time.time() - self._start_time
        return 0.0
