"""
Component base class and manager.
Similar to Datadog's component system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Component(ABC):
    """
    Base class for all agent components.
    
    Similar to Datadog's component interface:
    - Lifecycle: start(), stop()
    - Health: is_healthy()
    - Status: get_status()
    """
    
    def __init__(self, name: str):
        self.name = name
        self.running = False
    
    @abstractmethod
    async def start(self):
        """Start the component."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the component gracefully."""
        pass
    
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.running
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status."""
        return {
            "name": self.name,
            "running": self.running,
            "healthy": self.is_healthy(),
        }


class ComponentManager:
    """
    Manages all agent components.
    
    Similar to Datadog's component manager:
    - Register components
    - Start/stop all components
    - Health checks
    - Status reporting
    """
    
    def __init__(self):
        self.components: Dict[str, Component] = {}
    
    def register(self, name: str, component: Component):
        """Register a component."""
        self.components[name] = component
        logger.debug(f"Registered component: {name}")
    
    async def start_all(self):
        """Start all registered components."""
        for name, component in self.components.items():
            try:
                logger.info(f"Starting component: {name}")
                await component.start()
                component.running = True
            except Exception as e:
                logger.error(f"Failed to start component {name}: {e}")
                raise
    
    async def stop_all(self):
        """Stop all registered components."""
        # Stop in reverse order
        for name, component in reversed(list(self.components.items())):
            try:
                logger.info(f"Stopping component: {name}")
                await component.stop()
                component.running = False
            except Exception as e:
                logger.error(f"Error stopping component {name}: {e}")
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all components."""
        return {
            name: component.get_status()
            for name, component in self.components.items()
        }
    
    def get_component(self, name: str) -> Optional[Component]:
        """Get a component by name."""
        return self.components.get(name)
