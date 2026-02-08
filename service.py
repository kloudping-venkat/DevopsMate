"""
DevopsMate Intelligent Agent Service

4-Mode Operating System:
- ASK: Read-only intelligence
- PLAN: Change simulation
- DEBUG: Deep inspection
- EXECUTE: Real changes
"""

import logging
from typing import Optional
from uuid import UUID

from .modes import AskMode, PlanMode, DebugMode, ExecuteMode, AgentMode, AgentContext, ModeResult

logger = logging.getLogger(__name__)


class AgentService:
    """
    Main agent service that routes queries to appropriate modes
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.modes = {
            AgentMode.ASK: AskMode,
            AgentMode.PLAN: PlanMode,
            AgentMode.DEBUG: DebugMode,
            AgentMode.EXECUTE: ExecuteMode,
        }
    
    async def process_query(
        self,
        query: str,
        mode: AgentMode,
        user_id: UUID,
        tenant_id: UUID,
        session_id: str,
        permissions: list[str],
        scope: str = "default",
        **kwargs
    ) -> ModeResult:
        """
        Process a query in the specified mode
        
        Args:
            query: Natural language query
            mode: Agent mode (ASK, PLAN, DEBUG, EXECUTE)
            user_id: User making the query
            tenant_id: Tenant context
            session_id: Session identifier
            permissions: User permissions
            scope: Environment scope (staging, prod, etc.)
            **kwargs: Additional parameters for the query
        
        Returns:
            ModeResult with response and data
        """
        # Create context
        context = AgentContext(
            user_id=user_id,
            tenant_id=tenant_id,
            mode=mode,
            session_id=session_id,
            permissions=permissions,
            scope=scope,
            metadata=kwargs.get("metadata", {}),
        )
        
        # Get mode handler
        mode_class = self.modes.get(mode)
        if not mode_class:
            return ModeResult(
                success=False,
                mode=mode,
                query=query,
                response=f"Unknown mode: {mode}",
                errors=[f"Mode {mode} not supported"],
            )
        
        # Create mode instance and process
        try:
            # Pass db_session to modes that need it
            if mode in (AgentMode.ASK, AgentMode.PLAN, AgentMode.DEBUG, AgentMode.EXECUTE):
                mode_handler = mode_class(context, db_session=self.db_session)
            else:
                mode_handler = mode_class(context)
            result = await mode_handler.process(query, **kwargs)
            return result
        except Exception as e:
            logger.exception(f"Error processing query in {mode} mode: {e}")
            return ModeResult(
                success=False,
                mode=mode,
                query=query,
                response=f"Error processing query: {str(e)}",
                errors=[str(e)],
            )
    
    async def auto_detect_mode(self, query: str) -> AgentMode:
        """
        Auto-detect the appropriate mode from query intent
        
        Rules:
        - Questions → ASK
        - "What if", "Simulate", "Estimate" → PLAN
        - "Why", "Debug", "Diagnose" → DEBUG
        - "Deploy", "Scale", "Change" → EXECUTE (with approval)
        """
        query_lower = query.lower()
        
        # EXECUTE keywords (require explicit mode)
        if any(word in query_lower for word in ["deploy", "scale", "rollback", "change", "update", "modify"]):
            return AgentMode.EXECUTE
        
        # DEBUG keywords
        if any(word in query_lower for word in ["why", "debug", "diagnose", "trace", "analyze failure", "root cause"]):
            return AgentMode.DEBUG
        
        # PLAN keywords
        if any(word in query_lower for word in ["what if", "simulate", "estimate", "recommend", "should i", "plan"]):
            return AgentMode.PLAN
        
        # Default to ASK
        return AgentMode.ASK
    
    def get_mode_info(self, mode: AgentMode) -> dict:
        """Get information about a mode"""
        mode_info = {
            AgentMode.ASK: {
                "name": "ASK",
                "description": "Read-only intelligence & answers",
                "risk_level": "safe",
                "capabilities": [
                    "Read infrastructure",
                    "Read metrics/logs/traces",
                    "Health checks",
                    "Access verification",
                    "Cost analysis",
                ],
            },
            AgentMode.PLAN: {
                "name": "PLAN",
                "description": "Change simulation & recommendations",
                "risk_level": "medium",
                "capabilities": [
                    "Simulate changes",
                    "Estimate cost impact",
                    "Validate configurations",
                    "Recommend strategies",
                ],
            },
            AgentMode.DEBUG: {
                "name": "DEBUG",
                "description": "Deep inspection & diagnostics",
                "risk_level": "elevated",
                "capabilities": [
                    "Deep system inspection",
                    "Trace execution paths",
                    "Analyze failures",
                    "Diagnose root causes",
                ],
            },
            AgentMode.EXECUTE: {
                "name": "EXECUTE",
                "description": "Makes real changes",
                "risk_level": "high",
                "capabilities": [
                    "Deploy services",
                    "Scale infrastructure",
                    "Configure systems",
                    "Rollback changes",
                ],
                "requires_approval": True,
            },
        }
        
        return mode_info.get(mode, {})
