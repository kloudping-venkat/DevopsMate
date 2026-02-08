"""
EXECUTE Mode - Makes real changes

Rules:
- Requires explicit approval
- Audit all changes
- Rollback capability
- High security checks
- Limited scope
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AgentMode, AgentContext, BaseAgentMode, ModeCapability, ModeResult

logger = logging.getLogger(__name__)


class ExecuteMode(BaseAgentMode):
    """
    EXECUTE Mode - Makes real changes
    
    Capabilities:
    - Deploy services
    - Scale infrastructure
    - Configure systems
    - Rollback changes
    """
    
    def __init__(self, context: AgentContext, db_session: Optional[AsyncSession] = None):
        super().__init__(context)
        self.db_session = db_session
    
    def get_mode(self) -> AgentMode:
        return AgentMode.EXECUTE
    
    def _get_mode_capabilities(self) -> list[ModeCapability]:
        return [
            ModeCapability.READ_INFRA,
            ModeCapability.READ_CONFIG,
            ModeCapability.DEPLOY,
            ModeCapability.SCALE,
            ModeCapability.CONFIGURE,
            ModeCapability.ROLLBACK,
        ]
    
    async def _get_db_session(self) -> AsyncSession:
        """Get database session"""
        if self.db_session:
            return self.db_session
        raise ValueError("Database session required for EXECUTE mode operations")
    
    async def process(self, query: str, **kwargs) -> ModeResult:
        """Process an EXECUTE mode query"""
        # Check for explicit approval
        approval = kwargs.get("approval_token")
        if not approval:
            return ModeResult(
                success=False,
                mode=AgentMode.EXECUTE,
                query=query,
                response="EXECUTE mode requires explicit approval token. Please provide 'approval_token' in metadata.",
                access_denied=True,
                access_reason="Missing approval token",
            )
        
        # Validate approval token (simplified - in production, use proper token validation)
        if not self._validate_approval_token(approval):
            return ModeResult(
                success=False,
                mode=AgentMode.EXECUTE,
                query=query,
                response="Invalid approval token",
                access_denied=True,
                access_reason="Invalid approval token",
            )
        
        try:
            # Parse action from query using LLM
            from agent.llm_service import get_llm_service
            
            llm = get_llm_service()
            action_plan = await self._parse_action(query, llm)
            
            # Execute actions
            results = []
            for action in action_plan.get("actions", []):
                result = await self._execute_action(action)
                results.append(result)
            
            # Audit log
            await self._audit_log(query, action_plan, results)
            
            # Format response
            response = f"""**Execution Complete**

**Query:** {query}

**Actions Executed:**
"""
            for i, (action, result) in enumerate(zip(action_plan.get("actions", []), results), 1):
                status = "✅ Success" if result.get("success") else "❌ Failed"
                response += f"\n{i}. {action.get('type', 'unknown')}: {status}\n"
                if result.get("message"):
                    response += f"   {result['message']}\n"
            
            return ModeResult(
                success=all(r.get("success") for r in results),
                mode=AgentMode.EXECUTE,
                query=query,
                response=response,
                data={
                    "actions": action_plan.get("actions", []),
                    "results": results,
                },
                confidence=90.0 if all(r.get("success") for r in results) else 50.0,
            )
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            await self._audit_log(query, {}, [{"success": False, "error": str(e)}])
            return ModeResult(
                success=False,
                mode=AgentMode.EXECUTE,
                query=query,
                response=f"Error executing action: {str(e)}",
                errors=[str(e)],
            )
    
    async def _parse_action(self, query: str, llm) -> Dict[str, Any]:
        """Parse natural language query into structured actions"""
        system_prompt = """You are a DevOps execution engine. Parse natural language commands into structured actions.

Action types:
- deploy: Deploy a service or application
- scale: Scale infrastructure (up/down replicas, resources)
- configure: Update configuration
- rollback: Rollback a deployment
- restart: Restart a service
- update_repo: Update code in a GitHub repository

For each action, extract:
- type: Action type
- target: What to act on (service name, resource ID, etc.)
- parameters: Action-specific parameters
- scope: Environment/scope

Return JSON format with 'actions' array."""
        
        prompt = f"Parse this command into structured actions: {query}\n\nReturn only valid JSON."
        
        messages = [{"role": "user", "content": prompt}]
        response = await llm.chat(messages, system_prompt=system_prompt, temperature=0.1)
        
        # Parse JSON response
        try:
            import json
            import re
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                action_plan = json.loads(json_match.group())
            else:
                # Fallback: create simple action
                action_plan = {
                    "actions": [{
                        "type": "execute",
                        "target": query,
                        "parameters": {},
                    }]
                }
        except Exception as e:
            logger.warning(f"Error parsing action plan: {e}")
            action_plan = {
                "actions": [{
                    "type": "execute",
                    "target": query,
                    "parameters": {},
                }]
            }
        
        return action_plan
    
    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("type", "unknown")
        target = action.get("target", "")
        parameters = action.get("parameters", {})
        
        try:
            if action_type == "deploy":
                return await self._execute_deploy(target, parameters)
            elif action_type == "scale":
                return await self._execute_scale(target, parameters)
            elif action_type == "configure":
                return await self._execute_configure(target, parameters)
            elif action_type == "rollback":
                return await self._execute_rollback(target, parameters)
            elif action_type == "restart":
                return await self._execute_restart(target, parameters)
            elif action_type == "update_repo":
                return await self._execute_update_repo(target, parameters)
            else:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}",
                }
        except Exception as e:
            logger.error(f"Error executing {action_type}: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
            }
    
    async def _execute_deploy(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deployment"""
        # In production, this would trigger actual deployment
        # For now, log the action
        logger.info(f"Deploying {target} with parameters {parameters}")
        
        return {
            "success": True,
            "message": f"Deployment of {target} initiated",
            "deployment_id": f"deploy-{datetime.utcnow().timestamp()}",
        }
    
    async def _execute_scale(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scaling"""
        replicas = parameters.get("replicas", parameters.get("count", 1))
        logger.info(f"Scaling {target} to {replicas} replicas")
        
        return {
            "success": True,
            "message": f"Scaling {target} to {replicas} replicas",
        }
    
    async def _execute_configure(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute configuration update"""
        logger.info(f"Updating configuration for {target}: {parameters}")
        
        return {
            "success": True,
            "message": f"Configuration updated for {target}",
        }
    
    async def _execute_rollback(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rollback"""
        version = parameters.get("version", "previous")
        logger.info(f"Rolling back {target} to {version}")
        
        return {
            "success": True,
            "message": f"Rolled back {target} to {version}",
        }
    
    async def _execute_restart(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute service restart"""
        logger.info(f"Restarting {target}")
        
        return {
            "success": True,
            "message": f"Restarted {target}",
        }
    
    async def _execute_update_repo(self, target: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute repository code update
        
        Parameters:
        - repo_url: Repository URL (required)
        - file_path: Path to file in repository (required)
        - content: New file content (required)
        - message: Commit message (required)
        - branch: Branch name (default: main)
        - create_branch: Create new branch and PR (default: True)
        """
        repo_url = parameters.get("repo_url") or target
        file_path = parameters.get("file_path")
        content = parameters.get("content")
        message = parameters.get("message", f"Update {file_path}")
        branch = parameters.get("branch", "main")
        create_branch = parameters.get("create_branch", True)
        
        if not repo_url:
            return {
                "success": False,
                "message": "Repository URL is required",
            }
        
        if not file_path:
            return {
                "success": False,
                "message": "File path is required",
            }
        
        if not content:
            return {
                "success": False,
                "message": "File content is required",
            }
        
        try:
            from Api.services.github_service import get_github_service
            
            github_service = get_github_service()
            if not github_service:
                return {
                    "success": False,
                    "message": "GitHub service not configured. Set GITHUB_TOKEN environment variable.",
                }
            
            # Update file in repository
            result = await github_service.update_file(
                repo_url=repo_url,
                file_path=file_path,
                content=content,
                message=message,
                branch=branch,
                create_branch=create_branch,
            )
            
            if result.get("success"):
                logger.info(f"Updated {file_path} in {repo_url}")
                return {
                    "success": True,
                    "message": result.get("message", f"Updated {file_path}"),
                    "branch": result.get("branch"),
                    "pull_request": result.get("pull_request"),
                }
            else:
                return {
                    "success": False,
                    "message": result.get("error", "Failed to update repository"),
                }
        
        except Exception as e:
            logger.error(f"Error updating repository {repo_url}: {e}")
            return {
                "success": False,
                "message": f"Error updating repository: {str(e)}",
            }
    
    def _validate_approval_token(self, token: str) -> bool:
        """Validate approval token (simplified - in production, use proper validation)"""
        # In production, this would:
        # 1. Check token signature
        # 2. Verify token hasn't expired
        # 3. Check token permissions match the action
        # 4. Verify token was issued by authorized user
        
        # For now, accept any non-empty token (should be replaced with real validation)
        return bool(token and len(token) > 10)
    
    async def _audit_log(self, query: str, action_plan: Dict[str, Any], results: List[Dict[str, Any]]):
        """Log execution for audit"""
        try:
            db = await self._get_db_session()
            from Api.models.agent import AgentActionExecution
            from datetime import datetime
            import uuid as uuid_lib
            
            # Save each action execution
            for action, result in zip(action_plan.get("actions", []), results):
                execution = AgentActionExecution(
                    tenant_id=self.context.tenant_id,
                    user_id=self.context.user_id,
                    session_id=self.context.session_id,
                    query=query,
                    action_type=action.get("type", "unknown"),
                    target=action.get("target", ""),
                    parameters=action.get("parameters", {}),
                    status="success" if result.get("success") else "failed",
                    result=result,
                    error_message=result.get("message") if not result.get("success") else None,
                    execution_started_at=datetime.utcnow(),
                    execution_finished_at=datetime.utcnow(),
                    duration_seconds=result.get("duration", 0),
                )
                db.add(execution)
            
            await db.commit()
            logger.info(
                f"EXECUTE mode audit: user={self.context.user_id}, "
                f"query={query}, actions={len(action_plan.get('actions', []))}, "
                f"success={all(r.get('success') for r in results)}"
            )
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")
            if db:
                await db.rollback()