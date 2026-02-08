"""
DEBUG Mode - Deep inspection & diagnostics

Rules:
- Deep system inspection
- Trace execution paths
- Analyze failures
- Diagnose issues
- No changes, only inspection
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AgentMode, AgentContext, BaseAgentMode, ModeCapability, ModeResult

logger = logging.getLogger(__name__)


class DebugMode(BaseAgentMode):
    """
    DEBUG Mode - Deep inspection & diagnostics
    
    Capabilities:
    - Deep system inspection
    - Trace execution paths
    - Analyze failures
    - Diagnose root causes
    """
    
    def __init__(self, context: AgentContext, db_session: Optional[AsyncSession] = None):
        super().__init__(context)
        self.db_session = db_session
    
    def get_mode(self) -> AgentMode:
        return AgentMode.DEBUG
    
    def _get_mode_capabilities(self) -> list[ModeCapability]:
        return [
            ModeCapability.READ_INFRA,
            ModeCapability.READ_METRICS,
            ModeCapability.READ_LOGS,
            ModeCapability.READ_TRACES,
            ModeCapability.READ_TOPOLOGY,
            ModeCapability.DEEP_INSPECT,
            ModeCapability.TRACE_EXECUTION,
            ModeCapability.ANALYZE_FAILURE,
            ModeCapability.DIAGNOSE_ISSUE,
        ]
    
    async def _get_db_session(self) -> AsyncSession:
        """Get database session"""
        if self.db_session:
            return self.db_session
        raise ValueError("Database session required for DEBUG mode operations")
    
    async def process(self, query: str, **kwargs) -> ModeResult:
        """Process a DEBUG mode query"""
        try:
            from agent.llm_service import get_llm_service
            
            # Gather diagnostic data
            logs = await self._gather_logs(query, **kwargs)
            metrics = await self._gather_metrics(query, **kwargs)
            traces = await self._gather_traces(query, **kwargs)
            code = kwargs.get("code")
            context = await self._gather_context(query, **kwargs)
            
            # Use LLM to analyze
            llm = get_llm_service()
            analysis = await llm.analyze_issue(
                issue_description=query,
                logs=logs,
                metrics=metrics,
                code=code,
                context=context,
                traces=traces,
            )
            
            # Format response
            response = f"""**Root Cause Analysis**

**Issue:** {query}

**Root Cause:**
{analysis.get('root_cause', 'Analysis in progress...')}

**Evidence:**
"""
            for evidence in analysis.get('evidence', [])[:5]:
                response += f"- {evidence}\n"
            
            response += f"\n**Recommendations:**\n"
            for rec in analysis.get('recommendations', []):
                response += f"- {rec}\n"
            
            response += f"\n\n**Full Analysis:**\n{analysis.get('full_analysis', '')}"
            
            return ModeResult(
                success=True,
                mode=AgentMode.DEBUG,
                query=query,
                response=response,
                data={"analysis": analysis},
                confidence=85.0,
            )
        except Exception as e:
            logger.error(f"Error processing DEBUG query: {e}")
            return ModeResult(
                success=False,
                mode=AgentMode.DEBUG,
                query=query,
                response=f"Error analyzing issue: {str(e)}",
                errors=[str(e)],
            )
    
    async def _gather_logs(self, query: str, **kwargs) -> List[str]:
        """Gather relevant logs"""
        try:
            from Api.services.logs_service import LogsService
            from Api.schemas.logs import LogQuery, LogLevel
            
            logs_service = LogsService()
            db = await self._get_db_session()
            
            # Search for error logs
            now = datetime.utcnow()
            log_query = LogQuery(
                query=query,
                start_time=now - timedelta(hours=1),
                end_time=now,
                level=LogLevel.ERROR,
                limit=20,
            )
            
            result = await logs_service.search(self.context.tenant_id, log_query)
            if result and result.logs:
                return [log.body for log in result.logs]
        except Exception as e:
            logger.warning(f"Error gathering logs: {e}")
        
        return []
    
    async def _gather_metrics(self, query: str, **kwargs) -> Dict[str, Any]:
        """Gather relevant metrics"""
        try:
            from Api.services.metrics_service import MetricsService
            from Api.schemas.metrics import MetricQuery, AggregationType
            
            metrics_service = MetricsService()
            db = await self._get_db_session()
            
            now = datetime.utcnow()
            metrics = {}
            
            # Get error rate
            try:
                error_query = MetricQuery(
                    metric_name="service.errors.total",
                    start_time=now - timedelta(hours=1),
                    end_time=now,
                    aggregation=AggregationType.SUM,
                )
                error_series = await metrics_service.query(self.context.tenant_id, error_query, db)
                if error_series and error_series[0].values:
                    metrics["error_rate"] = error_series[0].values[-1]
            except Exception:
                pass
            
            # Get latency
            try:
                latency_query = MetricQuery(
                    metric_name="service.latency.p99",
                    start_time=now - timedelta(hours=1),
                    end_time=now,
                    aggregation=AggregationType.AVG,
                )
                latency_series = await metrics_service.query(self.context.tenant_id, latency_query, db)
                if latency_series and latency_series[0].values:
                    metrics["latency_p99"] = latency_series[0].values[-1]
            except Exception:
                pass
            
            return metrics
        except Exception as e:
            logger.warning(f"Error gathering metrics: {e}")
        
        return {}
    
    async def _gather_traces(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Gather relevant traces"""
        try:
            from Api.storage.clickhouse import get_clickhouse
            from sqlalchemy import and_
            
            client = get_clickhouse()
            now = datetime.utcnow()
            start_time = now - timedelta(hours=1)
            
            # Extract service name from query or kwargs
            service_name = kwargs.get("service")
            if not service_name:
                import re
                matches = re.findall(r'service[:\s]+(\w+)', query, re.IGNORECASE)
                if matches:
                    service_name = matches[0]
            
            # Build query conditions
            conditions = [f"tenant_id = '{self.context.tenant_id}'"]
            conditions.append(f"start_time >= '{start_time.isoformat()}'")
            conditions.append(f"start_time <= '{now.isoformat()}'")
            
            # Filter by error traces or specific service
            if kwargs.get("error_only", True):
                conditions.append("status_code = 'error'")
            
            if service_name:
                conditions.append(f"service_name = '{service_name}'")
            
            where_clause = " AND ".join(conditions)
            
            # Get error traces (limit to 10 most recent)
            trace_query = f"""
                SELECT DISTINCT trace_id
                FROM traces
                WHERE {where_clause}
                ORDER BY start_time DESC
                LIMIT 10
            """
            
            trace_result = client.query(trace_query)
            trace_ids = [row[0] for row in trace_result.result_rows]
            
            if not trace_ids:
                return []
            
            # Get spans for these traces
            trace_ids_str = "', '".join(trace_ids)
            spans_query = f"""
                SELECT 
                    trace_id,
                    span_id,
                    parent_span_id,
                    operation_name,
                    service_name,
                    start_time,
                    duration_ns,
                    status_code,
                    attributes
                FROM traces
                WHERE trace_id IN ('{trace_ids_str}')
                ORDER BY trace_id, start_time
                LIMIT 50
            """
            
            spans_result = client.query(spans_query)
            traces_data = []
            
            for row in spans_result.result_rows:
                traces_data.append({
                    "trace_id": row[0],
                    "span_id": row[1],
                    "parent_span_id": row[2],
                    "operation": row[3],
                    "service": row[4],
                    "start_time": str(row[5]),
                    "duration_ms": row[6] / 1000000 if row[6] else 0,
                    "status": row[7],
                    "attributes": row[8] if len(row) > 8 else {},
                })
            
            return traces_data
        except Exception as e:
            logger.warning(f"Error gathering traces: {e}")
        
        return []
    
    async def _gather_context(self, query: str, **kwargs) -> Dict[str, Any]:
        """Gather additional context"""
        context = {}
        
        try:
            db = await self._get_db_session()
            from Api.models.service import Service
            from sqlalchemy import and_
            
            # Extract service name from query if possible
            service_name = kwargs.get("service")
            if not service_name:
                # Try to extract from query
                import re
                matches = re.findall(r'service[:\s]+(\w+)', query, re.IGNORECASE)
                if matches:
                    service_name = matches[0]
            
            if service_name:
                service_result = await db.execute(
                    select(Service).where(
                        and_(
                            Service.tenant_id == str(self.context.tenant_id),
                            Service.name == service_name
                        )
                    )
                )
                service = service_result.scalar_one_or_none()
                if service:
                    context["service"] = {
                        "name": service.name,
                        "status": service.status,
                        "environment": service.environment,
                        "version": service.version,
                    }
        except Exception as e:
            logger.warning(f"Error gathering context: {e}")
        
        return context
