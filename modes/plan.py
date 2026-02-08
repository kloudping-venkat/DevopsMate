"""
PLAN Mode - Change simulation & recommendations

Rules:
- No actual changes
- Simulate changes
- Estimate impact
- Validate changes
- Provide recommendations
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AgentMode, AgentContext, BaseAgentMode, ModeCapability, ModeResult

logger = logging.getLogger(__name__)


class PlanMode(BaseAgentMode):
    """
    PLAN Mode - Change simulation & recommendations
    
    Capabilities:
    - Simulate infrastructure changes
    - Estimate cost impact
    - Validate configuration changes
    - Recommend deployment strategies
    """
    
    def __init__(self, context: AgentContext, db_session: Optional[AsyncSession] = None):
        super().__init__(context)
        self.db_session = db_session
    
    def get_mode(self) -> AgentMode:
        return AgentMode.PLAN
    
    def _get_mode_capabilities(self) -> list[ModeCapability]:
        return [
            ModeCapability.READ_INFRA,
            ModeCapability.READ_CONFIG,
            ModeCapability.READ_COST,
            ModeCapability.SIMULATE_CHANGE,
            ModeCapability.ESTIMATE_COST,
            ModeCapability.ESTIMATE_IMPACT,
            ModeCapability.VALIDATE_CHANGE,
        ]
    
    async def _get_db_session(self) -> AsyncSession:
        """Get database session"""
        if self.db_session:
            return self.db_session
        raise ValueError("Database session required for PLAN mode operations")
    
    async def process(self, query: str, **kwargs) -> ModeResult:
        """Process a PLAN mode query"""
        try:
            from agent.llm_service import get_llm_service
            
            # Gather context
            context = await self._gather_context()
            constraints = kwargs.get("constraints", [])
            
            # Use LLM to generate plan
            llm = get_llm_service()
            plan = await llm.generate_plan(
                goal=query,
                constraints=constraints,
                context=context,
            )
            
            # Format response
            response = f"""**Plan Generated for: {query}**

**Steps:**
"""
            for i, step in enumerate(plan.get("steps", []), 1):
                response += f"\n{i}. {step.get('description', 'Step')}\n"
                if step.get("details"):
                    for detail in step["details"]:
                        response += f"   - {detail}\n"
            
            response += f"\n\n**Full Plan:**\n{plan.get('raw_text', '')}"
            
            return ModeResult(
                success=True,
                mode=AgentMode.PLAN,
                query=query,
                response=response,
                data={"plan": plan},
                confidence=80.0,
            )
        except Exception as e:
            logger.error(f"Error processing PLAN query: {e}")
            return ModeResult(
                success=False,
                mode=AgentMode.PLAN,
                query=query,
                response=f"Error generating plan: {str(e)}",
                errors=[str(e)],
            )
    
    async def _gather_context(self) -> Dict[str, Any]:
        """Gather context for planning"""
        context = {}
        
        try:
            db = await self._get_db_session()
            from Api.models.service import Service
            from Api.models.host import Host
            
            # Get current infrastructure
            services_result = await db.execute(
                select(Service).where(
                    Service.tenant_id == str(self.context.tenant_id)
                ).limit(20)
            )
            services = services_result.scalars().all()
            context["services"] = [
                {
                    "name": s.name,
                    "type": s.service_type,
                    "environment": s.environment,
                    "status": s.status,
                }
                for s in services
            ]
            
            hosts_result = await db.execute(
                select(Host).where(
                    Host.tenant_id == self.context.tenant_id
                ).limit(20)
            )
            hosts = hosts_result.scalars().all()
            context["hosts"] = [
                {
                    "hostname": h.hostname,
                    "cloud_provider": h.cloud_provider,
                    "instance_type": h.cloud_instance_type,
                }
                for h in hosts
            ]
            
            context["scope"] = self.context.scope
            context["tenant_id"] = str(self.context.tenant_id)
        except Exception as e:
            logger.warning(f"Error gathering context: {e}")
        
        return context
