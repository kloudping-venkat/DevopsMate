"""
Component protocols/interfaces.
Similar to Datadog's component interface system.
"""

from typing import Protocol, runtime_checkable, Dict, Any, Optional
from abc import ABC, abstractmethod


@runtime_checkable
class ComponentProtocol(Protocol):
    """Protocol for all components."""
    
    name: str
    running: bool
    
    async def start(self) -> None:
        """Start the component."""
        ...
    
    async def stop(self) -> None:
        """Stop the component."""
        ...
    
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        ...
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status."""
        ...


@runtime_checkable
class CollectorProtocol(Protocol):
    """Protocol for collectors."""
    
    name: str
    interval: float
    
    async def collect(self) -> None:
        """Collect data."""
        ...
    
    async def stop(self) -> None:
        """Stop the collector."""
        ...


@runtime_checkable
class ForwarderProtocol(Protocol):
    """Protocol for forwarders."""
    
    async def start(self) -> None:
        """Start the forwarder."""
        ...
    
    async def stop(self) -> None:
        """Stop the forwarder."""
        ...
    
    async def flush(self) -> None:
        """Flush all buffers."""
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """Get forwarder statistics."""
        ...


@runtime_checkable
class CheckProtocol(Protocol):
    """Protocol for checks."""
    
    name: str
    
    async def check(self, instance: Optional[Dict[str, Any]] = None) -> Any:
        """Run the check."""
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """Get check statistics."""
        ...
