"""
Check interface - base class for all checks/collectors.
Similar to Datadog's pkg/collector/check structure.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CheckResult:
    """Result of a check execution."""
    status: str  # ok, warning, error
    metrics: List[Dict[str, Any]]
    events: List[Dict[str, Any]] = None
    service_checks: List[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.events is None:
            self.events = []
        if self.service_checks is None:
            self.service_checks = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class Check(ABC):
    """
    Base class for all checks/collectors.
    
    Similar to Datadog's check interface:
    - check() method to run the check
    - get_metrics() to get collected metrics
    - get_service_checks() to get service checks
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.instance_id = None
        self.last_result: Optional[CheckResult] = None
        self.run_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def check(self, instance: Optional[Dict[str, Any]] = None) -> CheckResult:
        """
        Run the check.
        
        Args:
            instance: Optional instance configuration
            
        Returns:
            CheckResult with metrics, events, etc.
        """
        pass
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get collected metrics from last run."""
        if self.last_result:
            return self.last_result.metrics
        return []
    
    def get_service_checks(self) -> List[Dict[str, Any]]:
        """Get service checks from last run."""
        if self.last_result:
            return self.last_result.service_checks
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get check statistics."""
        return {
            "name": self.name,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_run": self.last_result.timestamp.isoformat() if self.last_result else None,
            "last_status": self.last_result.status if self.last_result else None,
        }
