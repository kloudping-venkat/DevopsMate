"""
Base classes for agent modes
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class AgentMode(str, Enum):
    """Agent operating modes"""
    ASK = "ask"
    PLAN = "plan"
    DEBUG = "debug"
    EXECUTE = "execute"


class ModeCapability(str, Enum):
    """Capabilities available in each mode"""
    # ASK mode capabilities
    READ_INFRA = "read_infra"
    READ_METRICS = "read_metrics"
    READ_LOGS = "read_logs"
    READ_TRACES = "read_traces"
    READ_CONFIG = "read_config"
    READ_TOPOLOGY = "read_topology"
    READ_COST = "read_cost"
    READ_SECURITY = "read_security"
    READ_CICD = "read_cicd"
    
    # PLAN mode capabilities
    SIMULATE_CHANGE = "simulate_change"
    ESTIMATE_COST = "estimate_cost"
    ESTIMATE_IMPACT = "estimate_impact"
    VALIDATE_CHANGE = "validate_change"
    
    # DEBUG mode capabilities
    DEEP_INSPECT = "deep_inspect"
    TRACE_EXECUTION = "trace_execution"
    ANALYZE_FAILURE = "analyze_failure"
    DIAGNOSE_ISSUE = "diagnose_issue"
    
    # EXECUTE mode capabilities
    DEPLOY = "deploy"
    SCALE = "scale"
    CONFIGURE = "configure"
    ROLLBACK = "rollback"


@dataclass
class ModeResult:
    """Result from an agent mode operation"""
    success: bool
    mode: AgentMode
    query: str
    response: str
    data: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0  # 0-100
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    access_denied: bool = False
    access_reason: Optional[str] = None


@dataclass
class AgentContext:
    """Context for agent operations"""
    user_id: UUID
    tenant_id: UUID
    mode: AgentMode
    session_id: str
    permissions: List[str] = field(default_factory=list)
    scope: str = "default"  # staging, prod, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgentMode(ABC):
    """Base class for all agent modes"""
    
    def __init__(self, context: AgentContext):
        self.context = context
        self.mode = self.get_mode()
    
    @abstractmethod
    def get_mode(self) -> AgentMode:
        """Return the mode this class implements"""
        pass
    
    @abstractmethod
    async def process(self, query: str, **kwargs) -> ModeResult:
        """Process a query in this mode"""
        pass
    
    async def check_permission(
        self,
        capability: ModeCapability,
        resource: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has permission for this capability
        
        Returns: (allowed, reason_if_denied)
        """
        # Check mode-specific permissions
        if not self._has_mode_permission(capability):
            return False, f"Capability {capability.value} not available in {self.mode.value} mode"
        
        # Check user permissions
        if not self._has_user_permission(capability, resource):
            return False, f"User does not have permission for {capability.value}"
        
        # Check scope restrictions
        if not self._check_scope_restriction(resource):
            return False, f"Resource {resource} not accessible in scope {self.context.scope}"
        
        return True, None
    
    def _has_mode_permission(self, capability: ModeCapability) -> bool:
        """Check if capability is allowed in this mode"""
        mode_capabilities = self._get_mode_capabilities()
        return capability in mode_capabilities
    
    @abstractmethod
    def _get_mode_capabilities(self) -> List[ModeCapability]:
        """Return list of capabilities available in this mode"""
        pass
    
    def _has_user_permission(self, capability: ModeCapability, resource: Optional[str]) -> bool:
        """Check if user has permission for this capability"""
        # Check explicit permissions
        required_permission = f"{self.mode.value}:{capability.value}"
        if required_permission in self.context.permissions:
            return True
        
        # Check wildcard permissions
        if f"{self.mode.value}:*" in self.context.permissions:
            return True
        
        return False
    
    def _check_scope_restriction(self, resource: Optional[str]) -> bool:
        """Check if resource is accessible in current scope"""
        # In ASK mode, scope restrictions are more lenient
        # In EXECUTE mode, scope restrictions are strict
        if self.mode == AgentMode.ASK:
            # ASK mode can read across scopes (with proper permissions)
            return True
        elif self.mode == AgentMode.EXECUTE:
            # EXECUTE mode restricted to current scope
            if resource and not resource.startswith(self.context.scope):
                return False
        
        return True
