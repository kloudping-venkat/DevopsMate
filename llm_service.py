"""
LLM Service for DevopsMate Agent

Provides LLM capabilities for:
- Natural language understanding
- Question answering
- Plan generation
- Root cause analysis
- Code/issue analysis
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers - Ollama only (local, free)"""
    OLLAMA = "ollama"  # Local models via Ollama


class TaskType(str, Enum):
    """Task types for intelligent model routing"""
    # Code-focused tasks -> qwen2.5-coder:32b
    CODE = "code"           # GitHub code analysis, code generation
    INFRASTRUCTURE = "infrastructure"  # Terraform, K8s YAML, SSL scripts
    PLAN = "plan"           # Deployment planning, PLAN mode
    EXECUTE = "execute"     # Action execution, EXECUTE mode
    
    # Analytics-focused tasks -> mixtral:8x7b
    LOGS = "logs"           # Log analysis, Logs Explorer
    METRICS = "metrics"     # Metrics analysis, dashboards
    RCA = "rca"             # Root cause analysis, DEBUG mode
    INCIDENTS = "incidents" # Incident management, alerts
    COST = "cost"           # Cost Intelligence, billing analysis
    
    # General (uses default model)
    GENERAL = "general"


class LLMService:
    """
    LLM Service for agent operations
    
    Uses Ollama (local, free) for all LLM capabilities.
    Configure via OLLAMA_BASE_URL environment variable (default: http://localhost:11434/v1)
    """
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider or self._detect_provider()
        self.model = model or self._get_default_model()
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
    
    def _detect_provider(self) -> LLMProvider:
        """Always use Ollama (local, free) - no paid API providers"""
        return LLMProvider.OLLAMA
    
    def _get_default_model(self, task_type: Optional[TaskType] = None) -> str:
        """Get default model with intelligent task-based routing"""
        import os
        
        # Check for environment variable override first
        env_model = os.getenv("OLLAMA_MODEL")
        if env_model and not task_type:
            return env_model
        
        # Dual-model routing for different task types
        return self._select_ollama_model(task_type)
    
    def _select_ollama_model(self, task_type: Optional[TaskType] = None) -> str:
        """
        Intelligent model selection for Ollama based on task type.
        
        Model routing:
        - Code/Infrastructure tasks -> qwen2.5-coder:32b (optimized for code)
        - Analytics tasks -> mixtral:8x7b (optimized for reasoning/analysis)
        """
        import os
        
        # Model configuration (can be overridden via env vars)
        CODE_MODEL = os.getenv("OLLAMA_CODE_MODEL", "qwen2.5-coder:32b")
        ANALYTICS_MODEL = os.getenv("OLLAMA_ANALYTICS_MODEL", "mixtral:8x7b")
        DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", CODE_MODEL)
        
        if not task_type:
            return DEFAULT_MODEL
        
        # Code-focused tasks -> qwen2.5-coder:32b
        code_tasks = {
            TaskType.CODE,
            TaskType.INFRASTRUCTURE,
            TaskType.PLAN,
            TaskType.EXECUTE,
        }
        
        # Analytics-focused tasks -> mixtral:8x7b
        analytics_tasks = {
            TaskType.LOGS,
            TaskType.METRICS,
            TaskType.RCA,
            TaskType.INCIDENTS,
            TaskType.COST,
        }
        
        if task_type in code_tasks:
            logger.info(f"Task type '{task_type.value}' -> using code model: {CODE_MODEL}")
            return CODE_MODEL
        elif task_type in analytics_tasks:
            logger.info(f"Task type '{task_type.value}' -> using analytics model: {ANALYTICS_MODEL}")
            return ANALYTICS_MODEL
        else:
            return DEFAULT_MODEL
    
    async def _get_client(self):
        """Get Ollama LLM client instance"""
        if self._client:
            return self._client
        
        # Ollama uses OpenAI-compatible API
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url=self.base_url or "http://localhost:11434/v1",
                api_key="ollama"  # Ollama doesn't require real API key
            )
        except ImportError:
            logger.warning("OpenAI SDK not installed for Ollama, using fallback")
            self._client = None
        
        return self._client
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        track_usage: bool = True,
        tenant_id: Optional[str] = None,
        query_id: Optional[str] = None,
        mode: Optional[str] = None,
        task_type: Optional[TaskType] = None,
    ) -> str:
        """
        Chat completion with LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            system_prompt: System prompt (prepended to messages)
            task_type: Optional task type for intelligent model routing (Ollama only)
        
        Returns:
            Generated text response
        """
        client = await self._get_client()
        
        if not client:
            # Fallback: return a basic response
            return self._fallback_response(messages)
        
        # Select model based on task type (for Ollama dual-model routing)
        active_model = self._get_default_model(task_type) if self.provider == LLMProvider.OLLAMA else self.model
        
        # Prepare messages
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        try:
            # Only Ollama is supported (local, free)
            if self.provider == LLMProvider.OLLAMA:
                response = await client.chat.completions.create(
                    model=active_model,
                    messages=chat_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                
                # Track usage (Ollama is free, but we still track for monitoring)
                if track_usage and hasattr(response, 'usage'):
                    await self._track_usage(
                        provider=self.provider.value,
                        model=active_model,
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens,
                        tenant_id=tenant_id,
                        query_id=query_id,
                        mode=mode,
                    )
                
                return content
            else:
                return self._fallback_response(messages)
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return self._fallback_response(messages)
    
    async def ask_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        use_rag: bool = True,
        tenant_id: Optional[str] = None,
        knowledge_base_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Ask a question with optional context and RAG
        
        Args:
            question: The question to ask
            context: Optional context data (will be formatted)
            system_prompt: Optional system prompt
            use_rag: Whether to use RAG for context retrieval
            tenant_id: Tenant ID for RAG retrieval
            knowledge_base_ids: Optional knowledge base IDs to search
        
        Returns:
            Answer to the question
        """
        # Use RAG if enabled and tenant_id provided
        if use_rag and tenant_id:
            try:
                from Api.services.rag_service import RAGService
                from sqlalchemy.ext.asyncio import AsyncSession
                
                # Get database session (this would be injected in production)
                # For now, we'll make RAG optional
                rag_context = None
                
                # Try to retrieve context from knowledge base
                # Note: This requires a database session, which should be passed in production
                # For now, we'll skip RAG if session is not available
                
            except Exception as e:
                logger.warning(f"RAG retrieval failed, falling back to basic context: {e}")
        
        default_system = """You are a senior DevOps engineer and SRE expert. 
You have deep knowledge of:
- Cloud platforms (AWS, Azure, GCP, Cloudflare)
- CI/CD pipelines (GitHub Actions, GitLab, Jenkins, Azure DevOps)
- Infrastructure as Code (Terraform, Ansible, CloudFormation)
- Container orchestration (Kubernetes, Docker Swarm)
- Monitoring and observability (Prometheus, Grafana, Datadog, Dynatrace)
- Security best practices
- Cost optimization

Provide accurate, concise, and actionable answers. When you don't know something, say so clearly."""
        
        system = system_prompt or default_system
        
        messages = []
        if context:
            context_str = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_str}\n\nQuestion: {question}"
            })
        else:
            messages.append({
                "role": "user",
                "content": question
            })
        
        return await self.chat(messages, system_prompt=system, temperature=0.3, task_type=TaskType.GENERAL)
    
    async def generate_plan(
        self,
        goal: str,
        constraints: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured plan
        
        Args:
            goal: The goal to achieve
            constraints: Optional constraints
            context: Optional context
        
        Returns:
            Structured plan with steps
        """
        system_prompt = """You are a DevOps planning expert. Generate clear, structured plans for infrastructure changes, deployments, and operations.

Your plans should include:
1. Clear steps in logical order
2. Prerequisites and dependencies
3. Risk assessment
4. Rollback procedures
5. Success criteria

Format your response as a structured plan that can be executed."""
        
        prompt = f"Goal: {goal}\n\n"
        if constraints:
            prompt += f"Constraints:\n" + "\n".join(f"- {c}" for c in constraints) + "\n\n"
        if context:
            prompt += f"Context:\n{self._format_context(context)}\n\n"
        prompt += "Generate a detailed, step-by-step plan:"
        
        messages = [{"role": "user", "content": prompt}]
        # Use code model for infrastructure planning (Terraform, K8s, deployments)
        plan_text = await self.chat(messages, system_prompt=system_prompt, temperature=0.5, task_type=TaskType.PLAN)
        
        # Parse plan into structured format
        return self._parse_plan(plan_text)
    
    async def analyze_issue(
        self,
        issue_description: str,
        logs: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        traces: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze an issue and identify root cause
        
        Args:
            issue_description: Description of the issue
            logs: Optional log entries
            metrics: Optional metrics data
            code: Optional code to analyze
            context: Optional additional context
            traces: Optional trace/span data
        
        Returns:
            Analysis with root cause and recommendations
        """
        system_prompt = """You are a senior SRE and debugging expert. Analyze issues systematically to identify root causes.

Your analysis should include:
1. Root cause identification
2. Evidence supporting your conclusion
3. Impact assessment
4. Recommended fixes
5. Prevention strategies

Be thorough but concise. Focus on actionable insights."""
        
        prompt = f"Issue: {issue_description}\n\n"
        
        if logs:
            prompt += f"Relevant Logs:\n" + "\n".join(logs[:20]) + "\n\n"  # Limit to 20 logs
        
        if metrics:
            prompt += f"Metrics:\n{self._format_context(metrics)}\n\n"
        
        if traces:
            # Format traces for analysis
            trace_summary = []
            for trace in traces[:10]:  # Limit to 10 traces
                trace_summary.append(
                    f"Trace {trace.get('trace_id', 'unknown')[:8]}: "
                    f"{trace.get('service', 'unknown')} - {trace.get('operation', 'unknown')} "
                    f"({trace.get('duration_ms', 0):.2f}ms, status: {trace.get('status', 'unknown')})"
                )
            prompt += f"Relevant Traces:\n" + "\n".join(trace_summary) + "\n\n"
        
        if code:
            prompt += f"Code:\n{code}\n\n"
        
        if context:
            prompt += f"Additional Context:\n{self._format_context(context)}\n\n"
        
        prompt += "Analyze this issue and identify the root cause:"
        
        messages = [{"role": "user", "content": prompt}]
        # Use analytics model for root cause analysis (logs, metrics, traces analysis)
        analysis_text = await self.chat(messages, system_prompt=system_prompt, temperature=0.3, task_type=TaskType.RCA)
        
        # Parse analysis
        return self._parse_analysis(analysis_text)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dict as readable text"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                import json
                lines.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse plan text into structured format"""
        lines = plan_text.split("\n")
        steps = []
        current_step = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect step markers
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or \
               line.startswith(("-", "*")) or \
               line.startswith("Step"):
                if current_step:
                    steps.append(current_step)
                current_step = {"description": line, "details": []}
            elif current_step:
                current_step["details"].append(line)
            else:
                # First line without marker
                if not steps:
                    steps.append({"description": line, "details": []})
        
        if current_step:
            steps.append(current_step)
        
        return {
            "steps": steps,
            "raw_text": plan_text,
        }
    
    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse analysis text into structured format"""
        # Extract root cause (look for "Root Cause:" or similar)
        root_cause = None
        recommendations = []
        evidence = []
        
        lines = analysis_text.split("\n")
        current_section = None
        
        for line in lines:
            line_lower = line.lower()
            if "root cause" in line_lower:
                root_cause = line.split(":", 1)[1].strip() if ":" in line else line
                current_section = "root_cause"
            elif "recommendation" in line_lower or "fix" in line_lower or "solution" in line_lower:
                current_section = "recommendations"
                if ":" in line:
                    recommendations.append(line.split(":", 1)[1].strip())
            elif "evidence" in line_lower or "supporting" in line_lower:
                current_section = "evidence"
            elif current_section == "recommendations" and line.strip().startswith(("-", "*", "1.", "2.")):
                recommendations.append(line.strip().lstrip("-*123456789. "))
            elif current_section == "evidence" and line.strip().startswith(("-", "*")):
                evidence.append(line.strip().lstrip("-* "))
        
        # If no structured sections found, use first paragraph as root cause
        if not root_cause:
            paragraphs = analysis_text.split("\n\n")
            root_cause = paragraphs[0] if paragraphs else analysis_text[:200]
        
        return {
            "root_cause": root_cause,
            "recommendations": recommendations if recommendations else ["See full analysis"],
            "evidence": evidence,
            "full_analysis": analysis_text,
        }
    
    async def _track_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        tenant_id: Optional[str] = None,
        query_id: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        """Track LLM usage for cost monitoring"""
        try:
            # Calculate estimated cost
            cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
            
            # Save to database if tenant_id provided
            if tenant_id:
                # Import here to avoid circular dependencies
                from sqlalchemy.ext.asyncio import AsyncSession
                from Api.models.agent import AgentLLMUsage
                import uuid as uuid_lib
                
                # Get database session (would need to be passed or retrieved)
                # For now, just log
                logger.info(
                    f"LLM usage: provider={provider}, model={model}, "
                    f"tokens={total_tokens}, cost=${cost:.6f}"
                )
        except Exception as e:
            logger.warning(f"Error tracking LLM usage: {e}")
    
    def _calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on provider and model"""
        # Ollama is free (local models), so cost is always 0
        if provider == "ollama":
            return 0.0
        
        # Default to 0 for any unknown providers
        return 0.0
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """Fallback response when LLM is not available"""
        last_message = messages[-1]["content"] if messages else ""
        
        return f"""I understand your request: {last_message[:100]}

However, Ollama LLM integration is not fully configured. To enable full LLM capabilities:

1. Install Ollama: https://ollama.ai
2. Pull recommended models:
   - ollama pull qwen2.5-coder:32b  # For code/infrastructure tasks
   - ollama pull mixtral:8x7b       # For analytics tasks
3. Ensure Ollama is running on http://localhost:11434
4. Install Python SDK: pip install openai

For now, I can only provide basic responses. Please configure Ollama for full functionality."""


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get global LLM service instance"""
    global _llm_service
    
    if not _llm_service:
        import os
        _llm_service = LLMService(
            base_url=os.getenv("OLLAMA_BASE_URL"),
        )
    
    return _llm_service
