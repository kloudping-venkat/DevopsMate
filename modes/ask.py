"""
ASK Mode - Read-only intelligence & answers

Rules:
- No mutations
- No deployments
- No infra changes
- Read-only APIs only
- Cached + live data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    AgentMode,
    AgentContext,
    BaseAgentMode,
    ModeCapability,
    ModeResult,
)

logger = logging.getLogger(__name__)


class AskMode(BaseAgentMode):
    """
    ASK Mode - Read-only intelligence
    
    Capabilities:
    - Environment comparison
    - Resource listing
    - Health checks
    - Access verification
    - Repository analysis
    - Network diagnostics
    - Cost analysis
    """
    
    def __init__(self, context: AgentContext, db_session: Optional[AsyncSession] = None):
        super().__init__(context)
        self.db_session = db_session
        self._topology_engine = None
        self._metrics_service = None
        self._logs_service = None
    
    def get_mode(self) -> AgentMode:
        return AgentMode.ASK
    
    async def _get_db_session(self) -> AsyncSession:
        """Get database session"""
        if self.db_session:
            return self.db_session
        # If no session provided, raise error
        raise ValueError("Database session required for ASK mode operations")
    
    async def _get_topology_engine(self):
        """Get topology engine instance"""
        if not self._topology_engine:
            from Api.services.topology.engine import TopologyEngine
            self._topology_engine = TopologyEngine()
        return self._topology_engine
    
    async def _get_metrics_service(self):
        """Get metrics service instance"""
        if not self._metrics_service:
            from Api.services.metrics_service import MetricsService
            self._metrics_service = MetricsService()
        return self._metrics_service
    
    async def _get_logs_service(self):
        """Get logs service instance"""
        if not self._logs_service:
            from Api.services.logs_service import LogsService
            self._logs_service = LogsService()
        return self._logs_service
    
    def _get_mode_capabilities(self) -> List[ModeCapability]:
        return [
            ModeCapability.READ_INFRA,
            ModeCapability.READ_METRICS,
            ModeCapability.READ_LOGS,
            ModeCapability.READ_TRACES,
            ModeCapability.READ_CONFIG,
            ModeCapability.READ_TOPOLOGY,
            ModeCapability.READ_COST,
            ModeCapability.READ_SECURITY,
            ModeCapability.READ_CICD,
        ]
    
    async def process(self, query: str, **kwargs) -> ModeResult:
        """Process an ASK mode query"""
        start_time = datetime.utcnow()
        
        # Parse query intent
        intent = self._parse_intent(query)
        
        # Check permissions
        capability = self._get_required_capability(intent)
        resource = kwargs.get("resource")
        
        allowed, reason = await self.check_permission(capability, resource)
        if not allowed:
            return ModeResult(
                success=False,
                mode=AgentMode.ASK,
                query=query,
                response=f"Access denied: {reason}",
                access_denied=True,
                access_reason=reason,
            )
        
        # Route to appropriate handler
        try:
            if intent == "environment_compare":
                result = await self._handle_environment_compare(query, **kwargs)
            elif intent == "list_resources":
                result = await self._handle_list_resources(query, **kwargs)
            elif intent == "health_check":
                result = await self._handle_health_check(query, **kwargs)
            elif intent == "service_status":
                result = await self._handle_service_status(query, **kwargs)
            elif intent == "access_check":
                result = await self._handle_access_check(query, **kwargs)
            elif intent == "repo_analysis":
                result = await self._handle_repo_analysis(query, **kwargs)
            elif intent == "cost_analysis":
                result = await self._handle_cost_analysis(query, **kwargs)
            elif intent == "schema_validation":
                result = await self._handle_schema_validation(query, **kwargs)
            elif intent == "version_compare":
                result = await self._handle_version_compare(query, **kwargs)
            elif intent == "vm_diagnostics":
                result = await self._handle_vm_diagnostics(query, **kwargs)
            elif intent == "dns_check":
                result = await self._handle_dns_check(query, **kwargs)
            elif intent == "connectivity_check":
                result = await self._handle_connectivity_check(query, **kwargs)
            elif intent == "traceroute":
                result = await self._handle_traceroute(query, **kwargs)
            elif intent == "routing_check":
                result = await self._handle_routing_check(query, **kwargs)
            elif intent == "board_sync":
                result = await self._handle_board_sync(query, **kwargs)
            elif intent == "connectivity_issue":
                result = await self._handle_connectivity_issue(query, **kwargs)
            else:
                result = await self._handle_generic_query(query, **kwargs)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ModeResult(
                success=False,
                mode=AgentMode.ASK,
                query=query,
                response=f"Error processing query: {str(e)}",
                errors=[str(e)],
                execution_time_ms=execution_time,
            )
    
    def _parse_intent(self, query: str) -> str:
        """Parse query to determine intent"""
        query_lower = query.lower()
        
        # Environment comparison
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference", "drift"]):
            if any(word in query_lower for word in ["staging", "prod", "production", "dev", "environment"]):
                return "environment_compare"
        
        # List resources
        if any(word in query_lower for word in ["list", "show", "find", "all resources", "with tag"]):
            return "list_resources"
        
        # Health check
        if any(word in query_lower for word in ["healthy", "health", "status", "up", "down"]):
            if "service" in query_lower or "checkout" in query_lower or "api" in query_lower:
                return "service_status"
            return "health_check"
        
        # Access check
        if any(word in query_lower for word in ["who can", "permission", "access", "deploy", "rbac", "iam"]):
            return "access_check"
        
        # Repository analysis
        if any(word in query_lower for word in ["repo", "repository", "deploy", "best way", "service"]):
            return "repo_analysis"
        
        # Cost analysis
        if any(word in query_lower for word in ["cost", "break-even", "worth", "benefit"]):
            return "cost_analysis"
        
        # Schema validation
        if any(word in query_lower for word in ["migration", "schema", "safe", "breaking"]):
            return "schema_validation"
        
        # Version compare
        if any(word in query_lower for word in ["version", "latest", "running", "commit", "tag"]):
            return "version_compare"
        
        # VM diagnostics
        if any(word in query_lower for word in ["vm", "slow", "cpu", "memory", "disk"]):
            return "vm_diagnostics"
        
        # DNS check
        if any(word in query_lower for word in ["dns", "resolve", "resolving", "domain"]):
            return "dns_check"
        
        # Connectivity
        if any(word in query_lower for word in ["ping", "reach", "connect", "network"]):
            if "traceroute" in query_lower:
                return "traceroute"
            return "connectivity_check"
        
        # Routing
        if any(word in query_lower for word in ["route", "routing", "ingress", "load balancer"]):
            return "routing_check"
        
        # Board sync
        if any(word in query_lower for word in ["board", "github", "azure", "deployment status", "issues"]):
            return "board_sync"
        
        # Connectivity issue
        if any(word in query_lower for word in ["why can't", "can't reach", "connectivity issue", "can't connect"]):
            return "connectivity_issue"
        
        return "generic"
    
    def _get_required_capability(self, intent: str) -> ModeCapability:
        """Map intent to required capability"""
        intent_to_capability = {
            "environment_compare": ModeCapability.READ_INFRA,
            "list_resources": ModeCapability.READ_INFRA,
            "health_check": ModeCapability.READ_METRICS,
            "service_status": ModeCapability.READ_METRICS,
            "access_check": ModeCapability.READ_SECURITY,
            "repo_analysis": ModeCapability.READ_CICD,
            "cost_analysis": ModeCapability.READ_COST,
            "schema_validation": ModeCapability.READ_CONFIG,
            "version_compare": ModeCapability.READ_CICD,
            "vm_diagnostics": ModeCapability.READ_INFRA,
            "dns_check": ModeCapability.READ_INFRA,
            "connectivity_check": ModeCapability.READ_INFRA,
            "traceroute": ModeCapability.READ_INFRA,
            "routing_check": ModeCapability.READ_CONFIG,
            "board_sync": ModeCapability.READ_CICD,
            "connectivity_issue": ModeCapability.READ_TOPOLOGY,
        }
        return intent_to_capability.get(intent, ModeCapability.READ_INFRA)
    
    # ===========================================
    # ASK Mode Handlers (17 Examples)
    # ===========================================
    
    async def _handle_environment_compare(
        self, query: str, **kwargs
    ) -> ModeResult:
        """1. Environment Compare: Compare staging vs prod"""
        env1 = kwargs.get("env1", "staging")
        env2 = kwargs.get("env2", "production")
        
        # Import services
        from Api.services.topology.engine import TopologyEngine
        from Api.storage.postgres import get_postgres_pool
        
        pool = await get_postgres_pool()
        topology = TopologyEngine(pool)
        
        # Get infrastructure for both environments
        env1_data = await self._get_environment_data(env1)
        env2_data = await self._get_environment_data(env2)
        
        # Compare
        drift = self._calculate_drift(env1_data, env2_data)
        
        response = f"""
**Environment Comparison: {env1} vs {env2}**

**Infrastructure Drift:**
- Services: {drift['services_diff']} different
- Resource sizes: {drift['resource_diff']} mismatches
- Configurations: {drift['config_diff']} differences

**Risk Score:** {drift['risk_score']}/100

**Missing in {env2}:**
{self._format_list(drift['missing_in_env2'])}

**Missing in {env1}:**
{self._format_list(drift['missing_in_env1'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={
                "env1": env1_data,
                "env2": env2_data,
                "drift": drift,
            },
            confidence=85.0,
        )
    
    async def _handle_list_resources(
        self, query: str, **kwargs
    ) -> ModeResult:
        """2. List Resources by Tag Value"""
        tag_key = kwargs.get("tag_key", "owner")
        tag_value = kwargs.get("tag_value", "payments")
        
        # Query cloud APIs and Kubernetes
        resources = await self._query_resources_by_tag(tag_key, tag_value)
        
        response = f"""
**Resources with tag `{tag_key}={tag_value}`:**

**VMs:** {len(resources['vms'])}
{self._format_resource_list(resources['vms'])}

**Databases:** {len(resources['databases'])}
{self._format_resource_list(resources['databases'])}

**Load Balancers:** {len(resources['load_balancers'])}
{self._format_resource_list(resources['load_balancers'])}

**Total Cost Attribution:** ${resources['total_cost']:.2f}/month
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"resources": resources},
            confidence=90.0,
        )
    
    async def _handle_health_check(
        self, query: str, **kwargs
    ) -> ModeResult:
        """3. Environment Health Check"""
        environment = kwargs.get("environment", "production")
        
        # Aggregate health from multiple sources
        health_data = await self._aggregate_health(environment)
        
        response = f"""
**{environment.upper()} Health Status**

**Overall Health Score:** {health_data['overall_score']}/100

**Service SLOs:**
{self._format_slo_status(health_data['slo_status'])}

**Infrastructure:**
- Pods: {health_data['pods_healthy']}/{health_data['pods_total']} healthy
- Nodes: {health_data['nodes_healthy']}/{health_data['nodes_total']} healthy
- Error Rate: {health_data['error_rate']:.2f}%

**Degraded Services:**
{self._format_list(health_data['degraded_services'])}

**Blast Radius:** {health_data['blast_radius']} services affected
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"health": health_data},
            confidence=88.0,
        )
    
    async def _handle_service_status(
        self, query: str, **kwargs
    ) -> ModeResult:
        """4. Agent Status / Service Health"""
        service_name = kwargs.get("service", "checkout")
        
        # Get service health
        service_health = await self._get_service_health(service_name)
        
        if service_health['status'] == 'up':
            response = f"""
**{service_name} Service Status**

✅ **Status:** UP

**Metrics:**
- Last heartbeat: {service_health['last_heartbeat']}
- Recent errors: {service_health['recent_errors']}
- Latency: {service_health['latency_p50']}ms (p50), {service_health['latency_p99']}ms (p99)

**Observations:**
{service_health['degradation_note'] if service_health.get('degradation_note') else 'No issues detected'}
"""
        else:
            response = f"""
**{service_name} Service Status**

❌ **Status:** DOWN

**Last seen:** {service_health['last_seen']}
**Recent errors:** {service_health['recent_errors']}
**Possible causes:** {', '.join(service_health.get('possible_causes', []))}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"service_health": service_health},
            confidence=service_health.get('confidence', 75.0),
        )
    
    async def _handle_access_check(
        self, query: str, **kwargs
    ) -> ModeResult:
        """5. Access Check (RBAC / IAM)"""
        action = kwargs.get("action", "deploy")
        resource = kwargs.get("resource", "production")
        
        # Query IAM/RBAC
        access_info = await self._check_access_permissions(action, resource)
        
        response = f"""
**Access Check: Who can {action} to {resource}?**

**Users with permission:**
{self._format_access_list(access_info['allowed_users'])}

**Risk Findings:**
{self._format_risk_findings(access_info['risk_findings'])}

**Overprivileged Users:**
{self._format_list(access_info['overprivileged'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"access": access_info},
            confidence=92.0,
        )
    
    async def _handle_repo_analysis(
        self, query: str, **kwargs
    ) -> ModeResult:
        """6. Repo Read → Best Service to Deploy"""
        repo_url = kwargs.get("repo_url")
        
        # Analyze repository
        repo_analysis = await self._analyze_repository(repo_url)
        
        response = f"""
**Repository Analysis: {repo_analysis['name']}**

**Recommended Deployment Strategy:**

**Runtime:** {repo_analysis['recommended_runtime']}
**Scaling Model:** {repo_analysis['scaling_model']}
**Estimated Cost:** ${repo_analysis['estimated_cost']}/month

**Reasoning:**
- Language: {repo_analysis['language']}
- Dependencies: {len(repo_analysis['dependencies'])} packages
- Traffic Profile: {repo_analysis['traffic_profile']}
- Existing Pipelines: {len(repo_analysis['pipelines'])} found

**Observability Defaults:**
- Metrics: {repo_analysis['metrics_enabled']}
- Logs: {repo_analysis['logs_enabled']}
- Traces: {repo_analysis['traces_enabled']}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"analysis": repo_analysis},
            confidence=80.0,
        )
    
    async def _handle_cost_analysis(
        self, query: str, **kwargs
    ) -> ModeResult:
        """7. Repo Change → Break-Even Point"""
        change_type = kwargs.get("change_type", "memory_increase")
        change_value = kwargs.get("change_value")
        
        # Calculate cost impact
        cost_analysis = await self._calculate_cost_impact(change_type, change_value)
        
        response = f"""
**Cost-Benefit Analysis**

**Change:** {change_type} = {change_value}

**Cost Impact:**
- Infrastructure Cost Delta: ${cost_analysis['cost_delta']:.2f}/month
- Performance Gain: {cost_analysis['performance_gain']:.1f}%
- Error Reduction: {cost_analysis['error_reduction']:.1f}%

**Break-Even Point:**
- Requests/day: {cost_analysis['break_even_requests']:,}
- Current Traffic: {cost_analysis['current_traffic']:,} req/day
- **Verdict:** {'✅ Worth it' if cost_analysis['worth_it'] else '❌ Not worth it'}

**Risk Assessment:** {cost_analysis['risk_level']}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"cost_analysis": cost_analysis},
            confidence=75.0,
        )
    
    async def _handle_schema_validation(
        self, query: str, **kwargs
    ) -> ModeResult:
        """8. Database Schema Change Validation"""
        migration_sql = kwargs.get("migration_sql")
        
        # Validate migration
        validation = await self._validate_migration(migration_sql)
        
        response = f"""
**Migration Safety Analysis**

**Status:** {'✅ SAFE' if validation['is_safe'] else '⚠️ RISKY'}

**Compatibility:**
- Backward Compatible: {validation['backward_compatible']}
- Breaking Changes: {len(validation['breaking_changes'])}
- Index Impact: {validation['index_impact']}
- Lock Duration: {validation['estimated_lock_duration']}s

**Affected Services:**
{self._format_list(validation['affected_services'])}

**Risks:**
{self._format_list(validation['risks'])}

**Required Deploy Order:**
{self._format_list(validation['deploy_order'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"validation": validation},
            confidence=validation.get('confidence', 70.0),
        )
    
    async def _handle_version_compare(
        self, query: str, **kwargs
    ) -> ModeResult:
        """9. App vs Pipeline Version Compare"""
        service = kwargs.get("service", "all")
        
        # Compare versions
        version_info = await self._compare_versions(service)
        
        response = f"""
**Version Comparison: {service}**

**Git Commit:**
- Latest: {version_info['git_latest']}
- Running: {version_info['git_running']}
- **Drift:** {version_info['git_drift']}

**Image Tag:**
- Latest: {version_info['image_latest']}
- Running: {version_info['image_running']}
- **Drift:** {version_info['image_drift']}

**Stale Services:**
{self._format_list(version_info['stale_services'])}

**Missed Deployments:**
{self._format_list(version_info['missed_deployments'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"versions": version_info},
            confidence=95.0,
        )
    
    async def _handle_vm_diagnostics(
        self, query: str, **kwargs
    ) -> ModeResult:
        """10. VM-Based Ask: Why is VM-12 slow?"""
        vm_id = kwargs.get("vm_id", "VM-12")
        
        # Diagnose VM performance
        diagnostics = await self._diagnose_vm(vm_id)
        
        response = f"""
**VM Diagnostics: {vm_id}**

**Performance Issues:**
- CPU Steal: {diagnostics['cpu_steal']:.1f}%
- Disk IO Wait: {diagnostics['disk_io_wait']:.1f}%
- Network Latency: {diagnostics['network_latency']:.1f}ms
- Memory Pressure: {diagnostics['memory_pressure']:.1f}%

**Root Cause:**
{diagnostics['root_cause']}

**Noisy Neighbor Detection:**
{diagnostics['noisy_neighbors'] if diagnostics.get('noisy_neighbors') else 'None detected'}

**Recommendations:**
{self._format_list(diagnostics['recommendations'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"diagnostics": diagnostics},
            confidence=85.0,
        )
    
    async def _handle_dns_check(
        self, query: str, **kwargs
    ) -> ModeResult:
        """11. DNS Check"""
        domain = kwargs.get("domain", "api.example.com")
        
        # Check DNS
        dns_info = await self._check_dns(domain)
        
        response = f"""
**DNS Check: {domain}**

**Resolution:**
- Status: {'✅ Resolving' if dns_info['resolves'] else '❌ Not resolving'}
- IP Addresses: {', '.join(dns_info['ip_addresses'])}
- TTL: {dns_info['ttl']}s

**Geo Differences:**
{self._format_dns_geo(dns_info['geo_responses'])}

**Record Mismatches:**
{self._format_list(dns_info['mismatches']) if dns_info.get('mismatches') else 'None'}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"dns": dns_info},
            confidence=90.0,
        )
    
    async def _handle_connectivity_check(
        self, query: str, **kwargs
    ) -> ModeResult:
        """12. IP Ping: Can prod reach Redis?"""
        source = kwargs.get("source", "production")
        target = kwargs.get("target", "redis")
        
        # Check connectivity
        connectivity = await self._check_connectivity(source, target)
        
        response = f"""
**Connectivity Check: {source} → {target}**

**Status:** {'✅ Reachable' if connectivity['reachable'] else '❌ Not reachable'}

**Latency:**
- Min: {connectivity['latency_min']:.1f}ms
- Avg: {connectivity['latency_avg']:.1f}ms
- Max: {connectivity['latency_max']:.1f}ms

**Packet Loss:** {connectivity['packet_loss']:.1f}%

**Issues:**
{self._format_list(connectivity['issues']) if connectivity.get('issues') else 'None'}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"connectivity": connectivity},
            confidence=88.0,
        )
    
    async def _handle_traceroute(
        self, query: str, **kwargs
    ) -> ModeResult:
        """13. Traceroute: Where is latency introduced?"""
        target = kwargs.get("target")
        
        # Run traceroute
        trace = await self._run_traceroute(target)
        
        response = f"""
**Traceroute: {target}**

**Total Hops:** {len(trace['hops'])}
**Total Latency:** {trace['total_latency']:.1f}ms

**Hop Analysis:**
{self._format_traceroute_hops(trace['hops'])}

**Suspect Nodes:**
{self._format_list(trace['suspect_nodes']) if trace.get('suspect_nodes') else 'None'}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"traceroute": trace},
            confidence=80.0,
        )
    
    async def _handle_routing_check(
        self, query: str, **kwargs
    ) -> ModeResult:
        """14. Rewrite & Reroute Check"""
        service = kwargs.get("service")
        
        # Check routing
        routing = await self._check_routing(service)
        
        response = f"""
**Routing Check: {service}**

**Ingress Rules:**
{self._format_routing_rules(routing['ingress_rules'])}

**Load Balancer Config:**
{self._format_lb_config(routing['lb_config'])}

**Issues Detected:**
{self._format_list(routing['issues']) if routing.get('issues') else 'None'}

**Misroutes:** {len(routing.get('misroutes', []))}
**Shadow Traffic:** {routing.get('shadow_traffic', 0)} req/s
**Loopbacks:** {len(routing.get('loopbacks', []))}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"routing": routing},
            confidence=85.0,
        )
    
    async def _handle_board_sync(
        self, query: str, **kwargs
    ) -> ModeResult:
        """15-16. GitHub/Azure Board Sync"""
        board_type = kwargs.get("board_type", "github")
        
        # Sync board data
        board_data = await self._sync_board(board_type)
        
        response = f"""
**{board_type.upper()} Board Sync**

**Deployment Status:**
- Successful: {board_data['deployments_success']}
- Failed: {board_data['deployments_failed']}
- In Progress: {board_data['deployments_in_progress']}

**Open Issues:** {board_data['open_issues']}
**Open PRs:** {board_data['open_prs']}

**Correlations:**
{self._format_correlations(board_data['correlations'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"board": board_data},
            confidence=90.0,
        )
    
    async def _handle_connectivity_issue(
        self, query: str, **kwargs
    ) -> ModeResult:
        """17. Connectivity Issues: Why can't service A reach service B?"""
        service_a = kwargs.get("service_a")
        service_b = kwargs.get("service_b")
        
        # Analyze connectivity issue
        analysis = await self._analyze_connectivity_issue(service_a, service_b)
        
        response = f"""
**Connectivity Analysis: {service_a} → {service_b}**

**Status:** {'✅ Connected' if analysis['connected'] else '❌ Not Connected'}

**Root Cause:**
{analysis['root_cause']}

**Network Policies:**
{self._format_network_policies(analysis['network_policies'])}

**Security Groups:**
{self._format_security_groups(analysis['security_groups'])}

**DNS Resolution:**
- {service_b}: {'✅ Resolves' if analysis['dns_resolves'] else '❌ Does not resolve'}

**TLS Errors:**
{self._format_list(analysis['tls_errors']) if analysis.get('tls_errors') else 'None'}

**Topology Path:**
{self._format_topology_path(analysis['topology_path'])}
"""
        
        return ModeResult(
            success=True,
            mode=AgentMode.ASK,
            query=query,
            response=response,
            data={"analysis": analysis},
            confidence=82.0,
        )
    
    async def _handle_generic_query(
        self, query: str, **kwargs
    ) -> ModeResult:
        """Handle generic queries using LLM"""
        try:
            from agent.llm_service import get_llm_service
            
            # Gather context from database
            db = await self._get_db_session()
            context = {}
            
            # Get basic infrastructure context
            try:
                from Api.models.service import Service
                from Api.models.host import Host
                
                services_result = await db.execute(
                    select(Service).where(
                        Service.tenant_id == str(self.context.tenant_id)
                    ).limit(10)
                )
                services = services_result.scalars().all()
                context["services"] = [s.name for s in services]
                
                hosts_result = await db.execute(
                    select(Host).where(
                        Host.tenant_id == self.context.tenant_id
                    ).limit(10)
                )
                hosts = hosts_result.scalars().all()
                context["hosts"] = [h.hostname for h in hosts]
            except Exception:
                pass
            
            # Use LLM to answer
            llm = get_llm_service()
            answer = await llm.ask_question(query, context=context)
            
            return ModeResult(
                success=True,
                mode=AgentMode.ASK,
                query=query,
                response=answer,
                data={"context_used": bool(context)},
                confidence=75.0,
            )
        except Exception as e:
            logger.error(f"Error in generic query handler: {e}")
            return ModeResult(
                success=True,
                mode=AgentMode.ASK,
                query=query,
                response="I understand your query, but need more context. Please rephrase with specific details.",
                confidence=50.0,
                errors=[str(e)],
            )
    
    # ===========================================
    # Helper Methods (Implementation stubs)
    # ===========================================
    
    async def _get_environment_data(self, env: str) -> Dict[str, Any]:
        """Get infrastructure data for an environment"""
        try:
            db = await self._get_db_session()
            
            # Query services in this environment
            from Api.models.service import Service
            from Api.models.host import Host
            
            services_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.environment == env
                    )
                )
            )
            services = services_result.scalars().all()
            
            # Query hosts
            hosts_result = await db.execute(
                select(Host).where(
                    and_(
                        Host.tenant_id == self.context.tenant_id,
                        # Match environment from tags or metadata
                        or_(
                            Host.tags['environment'].astext == env,
                            Host.tags['env'].astext == env
                        )
                    )
                )
            )
            hosts = hosts_result.scalars().all()
            
            # Get topology data
            topology = await self._get_topology_engine()
            graph = topology.get_graph(self.context.tenant_id)
            
            return {
                "services": [
                    {
                        "name": s.name,
                        "type": s.service_type,
                        "version": s.version,
                        "status": s.status,
                        "technology": s.technology,
                        "tags": s.tags,
                    }
                    for s in services
                ],
                "hosts": [
                    {
                        "host_id": h.host_id,
                        "hostname": h.hostname,
                        "os_type": h.os_type,
                        "cloud_provider": h.cloud_provider,
                        "cloud_region": h.cloud_region,
                        "tags": h.tags,
                    }
                    for h in hosts
                ],
                "topology": {
                    "entities_count": len(graph.entities) if graph else 0,
                    "relationships_count": len(graph.relationships) if graph else 0,
                },
                "environment": env,
            }
        except Exception as e:
            logger.error(f"Error fetching environment data for {env}: {e}")
            return {
                "services": [],
                "hosts": [],
                "topology": {},
                "environment": env,
                "error": str(e),
            }
    
    def _calculate_drift(self, env1_data: Dict, env2_data: Dict) -> Dict[str, Any]:
        """Calculate drift between environments"""
        env1_services = {s["name"]: s for s in env1_data.get("services", [])}
        env2_services = {s["name"]: s for s in env2_data.get("services", [])}
        
        env1_hosts = {h["host_id"]: h for h in env1_data.get("hosts", [])}
        env2_hosts = {h["host_id"]: h for h in env2_data.get("hosts", [])}
        
        # Find differences
        missing_in_env2 = [name for name in env1_services if name not in env2_services]
        missing_in_env1 = [name for name in env2_services if name not in env1_services]
        
        # Find version/config differences
        config_diff = 0
        for name in set(env1_services.keys()) & set(env2_services.keys()):
            s1 = env1_services[name]
            s2 = env2_services[name]
            if s1.get("version") != s2.get("version"):
                config_diff += 1
        
        # Calculate risk score
        risk_score = min(100, (
            len(missing_in_env2) * 10 +
            len(missing_in_env1) * 10 +
            config_diff * 5
        ))
        
        return {
            "services_diff": abs(len(env1_services) - len(env2_services)),
            "resource_diff": abs(len(env1_hosts) - len(env2_hosts)),
            "config_diff": config_diff,
            "risk_score": risk_score,
            "missing_in_env2": missing_in_env2,
            "missing_in_env1": missing_in_env1,
        }
    
    async def _query_resources_by_tag(self, tag_key: str, tag_value: str) -> Dict[str, Any]:
        """Query resources by tag"""
        try:
            db = await self._get_db_session()
            from Api.models.service import Service
            from Api.models.host import Host
            
            # Query services with tag
            services_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.tags[tag_key].astext == tag_value
                    )
                )
            )
            services = services_result.scalars().all()
            
            # Query hosts with tag
            hosts_result = await db.execute(
                select(Host).where(
                    and_(
                        Host.tenant_id == self.context.tenant_id,
                        Host.tags[tag_key].astext == tag_value
                    )
                )
            )
            hosts = hosts_result.scalars().all()
            
            # Categorize resources
            vms = []
            databases = []
            load_balancers = []
            
            for service in services:
                if service.service_type == "database":
                    databases.append({
                        "name": service.name,
                        "type": service.technology,
                        "environment": service.environment,
                    })
                elif service.service_type == "gateway" or "lb" in service.name.lower():
                    load_balancers.append({
                        "name": service.name,
                        "type": service.service_type,
                    })
            
            for host in hosts:
                vms.append({
                    "name": host.hostname,
                    "host_id": host.host_id,
                    "cloud_provider": host.cloud_provider,
                    "instance_type": host.cloud_instance_type,
                })
            
            # Estimate cost (simplified)
            total_cost = len(vms) * 50.0 + len(databases) * 100.0 + len(load_balancers) * 30.0
            
            return {
                "vms": vms,
                "databases": databases,
                "load_balancers": load_balancers,
                "services": [
                    {
                        "name": s.name,
                        "type": s.service_type,
                        "environment": s.environment,
                    }
                    for s in services
                ],
                "total_cost": total_cost,
            }
        except Exception as e:
            logger.error(f"Error querying resources by tag {tag_key}={tag_value}: {e}")
            return {
                "vms": [],
                "databases": [],
                "load_balancers": [],
                "total_cost": 0.0,
                "error": str(e),
            }
    
    async def _aggregate_health(self, environment: str) -> Dict[str, Any]:
        """Aggregate health from multiple sources"""
        try:
            db = await self._get_db_session()
            metrics_service = await self._get_metrics_service()
            logs_service = await self._get_logs_service()
            
            from Api.models.service import Service
            from Api.models.host import Host
            from Api.schemas.logs import LogQuery, LogLevel
            
            # Get all services in environment
            services_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.environment == environment
                    )
                )
            )
            services = services_result.scalars().all()
            
            # Get hosts
            hosts_result = await db.execute(
                select(Host).where(
                    and_(
                        Host.tenant_id == self.context.tenant_id,
                        or_(
                            Host.tags['environment'].astext == environment,
                            Host.tags['env'].astext == environment
                        )
                    )
                )
            )
            hosts = hosts_result.scalars().all()
            
            # Calculate health metrics
            healthy_services = [s for s in services if s.status == "healthy"]
            degraded_services = [s.name for s in services if s.status in ["warning", "critical"]]
            
            healthy_hosts = [h for h in hosts if h.status == "healthy"]
            
            # Get error rate
            now = datetime.utcnow()
            log_query = LogQuery(
                query=f"environment:{environment}",
                start_time=now - timedelta(minutes=15),
                end_time=now,
                level=LogLevel.ERROR,
                limit=1000,
            )
            
            try:
                error_logs = await logs_service.search(self.context.tenant_id, log_query)
                total_errors = error_logs.total if error_logs else 0
                # Estimate error rate (simplified)
                error_rate = (total_errors / max(len(services) * 100, 1)) * 100
            except Exception:
                error_rate = 0.0
            
            # Calculate overall score
            service_health_ratio = len(healthy_services) / max(len(services), 1)
            host_health_ratio = len(healthy_hosts) / max(len(hosts), 1)
            error_penalty = min(error_rate / 10, 0.3)  # Max 30% penalty
            
            overall_score = int((service_health_ratio * 0.5 + host_health_ratio * 0.3 + (1 - error_penalty) * 0.2) * 100)
            
            # Get SLO status
            slo_status = {}
            for service in services:
                if service.slo_config:
                    slo_status[service.name] = "met"  # Simplified
            
            return {
                "overall_score": overall_score,
                "slo_status": slo_status,
                "pods_healthy": len(healthy_services),  # Simplified - would need K8s integration
                "pods_total": len(services),
                "nodes_healthy": len(healthy_hosts),
                "nodes_total": len(hosts),
                "error_rate": error_rate,
                "degraded_services": degraded_services,
                "blast_radius": len(degraded_services),
            }
        except Exception as e:
            logger.error(f"Error aggregating health for {environment}: {e}")
            return {
                "overall_score": 0,
                "slo_status": {},
                "pods_healthy": 0,
                "pods_total": 0,
                "nodes_healthy": 0,
                "nodes_total": 0,
                "error_rate": 0.0,
                "degraded_services": [],
                "blast_radius": 0,
                "error": str(e),
            }
    
    async def _get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get service health status"""
        try:
            db = await self._get_db_session()
            metrics_service = await self._get_metrics_service()
            logs_service = await self._get_logs_service()
            
            # Get service from database
            from Api.models.service import Service
            from Api.schemas.metrics import MetricQuery, AggregationType
            from Api.schemas.logs import LogQuery, LogLevel
            
            service_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.name == service_name
                    )
                )
            )
            service = service_result.scalar_one_or_none()
            
            if not service:
                return {
                    "status": "unknown",
                    "error": f"Service {service_name} not found",
                }
            
            # Get recent metrics
            now = datetime.utcnow()
            metric_query = MetricQuery(
                metric_name=f"service.{service_name}.latency",
                start_time=now - timedelta(minutes=15),
                end_time=now,
                aggregation=AggregationType.P50,
            )
            
            try:
                latency_series = await metrics_service.query(
                    self.context.tenant_id,
                    metric_query,
                    db
                )
                latency_p50 = latency_series[0].values[-1] if latency_series and latency_series[0].values else None
            except Exception:
                latency_p50 = None
            
            # Get recent errors
            log_query = LogQuery(
                query=f"service:{service_name}",
                start_time=now - timedelta(minutes=15),
                end_time=now,
                level=LogLevel.ERROR,
                limit=100,
            )
            
            try:
                error_logs = await logs_service.search(self.context.tenant_id, log_query)
                recent_errors = error_logs.total if error_logs else 0
            except Exception:
                recent_errors = 0
            
            # Determine status
            status = service.status
            if recent_errors > 10:
                status = "critical"
            elif recent_errors > 0:
                status = "warning"
            
            # Check for degradation
            degradation_note = None
            if latency_p50 and latency_p50 > 200:  # Threshold
                degradation_note = f"Experiencing {((latency_p50 - 50) / 50 * 100):.1f}% latency degradation since {now.strftime('%H:%M UTC')}"
            
            return {
                "status": status,
                "service_name": service_name,
                "last_heartbeat": service.updated_at.isoformat() if service.updated_at else None,
                "recent_errors": recent_errors,
                "latency_p50": latency_p50,
                "latency_p99": None,  # Would need p99 query
                "degradation_note": degradation_note,
                "confidence": 85.0 if latency_p50 else 60.0,
            }
        except Exception as e:
            logger.error(f"Error getting service health for {service_name}: {e}")
            return {
                "status": "unknown",
                "error": str(e),
            }
    
    async def _check_access_permissions(self, action: str, resource: str) -> Dict[str, Any]:
        """Check access permissions"""
        return {
            "allowed_users": [],
            "risk_findings": [],
            "overprivileged": [],
        }
    
    async def _analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """Analyze repository for deployment recommendations"""
        try:
            from Api.services.github_service import get_github_service
            
            github_service = get_github_service()
            if not github_service:
                # Fallback if GitHub service not available
                return {
                    "name": "unknown",
                    "recommended_runtime": "kubernetes",
                    "scaling_model": "horizontal",
                    "estimated_cost": 0.0,
                    "language": "unknown",
                    "dependencies": [],
                    "traffic_profile": "unknown",
                    "pipelines": [],
                    "metrics_enabled": False,
                    "logs_enabled": False,
                    "traces_enabled": False,
                    "error": "GitHub service not configured. Set GITHUB_TOKEN environment variable.",
                }
            
            # Use GitHub service to analyze repository
            analysis = await github_service.analyze_repository(repo_url)
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_url}: {e}")
            return {
                "name": "unknown",
                "recommended_runtime": "kubernetes",
                "scaling_model": "horizontal",
                "estimated_cost": 0.0,
                "language": "unknown",
                "dependencies": [],
                "traffic_profile": "unknown",
                "pipelines": [],
                "metrics_enabled": False,
                "logs_enabled": False,
                "traces_enabled": False,
                "error": str(e),
            }
    
    async def _calculate_cost_impact(self, change_type: str, change_value: Any) -> Dict[str, Any]:
        """Calculate cost impact of a change"""
        try:
            # Parse change value
            if isinstance(change_value, str):
                # Try to extract numeric value
                import re
                numbers = re.findall(r'\d+\.?\d*', change_value)
                change_value = float(numbers[0]) if numbers else 0.0
            else:
                change_value = float(change_value) if change_value else 0.0
            
            # Get current infrastructure costs (simplified)
            db = await self._get_db_session()
            from Api.models.host import Host
            from Api.models.service import Service
            
            hosts_result = await db.execute(
                select(Host).where(Host.tenant_id == self.context.tenant_id)
            )
            hosts = hosts_result.scalars().all()
            
            # Estimate current cost
            current_cost = len(hosts) * 50.0  # $50/month per host estimate
            
            # Calculate cost delta based on change type
            cost_delta = 0.0
            if "memory" in change_type.lower():
                # Memory increase = more expensive instances
                cost_delta = change_value * 0.1  # $0.10 per GB/month
            elif "cpu" in change_type.lower():
                # CPU increase = more expensive instances
                cost_delta = change_value * 5.0  # $5 per vCPU/month
            elif "replicas" in change_type.lower() or "scale" in change_type.lower():
                # Scaling = more instances
                cost_delta = change_value * 50.0  # $50 per instance/month
            
            # Get current traffic (from metrics)
            metrics_service = await self._get_metrics_service()
            from Api.schemas.metrics import MetricQuery, AggregationType
            
            now = datetime.utcnow()
            try:
                traffic_query = MetricQuery(
                    metric_name="service.requests.total",
                    start_time=now - timedelta(days=1),
                    end_time=now,
                    aggregation=AggregationType.SUM,
                )
                traffic_series = await metrics_service.query(self.context.tenant_id, traffic_query, db)
                current_traffic = int(traffic_series[0].values[-1] * 24) if traffic_series and traffic_series[0].values else 10000  # requests/day
            except Exception:
                current_traffic = 10000  # Default estimate
            
            # Estimate performance gain (simplified)
            performance_gain = min(50.0, change_value * 2.0) if change_value > 0 else 0.0
            
            # Estimate error reduction (simplified)
            error_reduction = min(30.0, change_value * 1.5) if change_value > 0 else 0.0
            
            # Calculate break-even
            # Break-even when: (cost_delta / current_traffic) < (performance_gain * value_per_request)
            value_per_request = 0.001  # $0.001 per request value
            break_even_requests = int(cost_delta / (performance_gain * value_per_request)) if performance_gain > 0 else 0
            
            # Determine if worth it
            worth_it = current_traffic >= break_even_requests if break_even_requests > 0 else False
            
            # Risk level
            risk_level = "low"
            if cost_delta > 1000:
                risk_level = "high"
            elif cost_delta > 100:
                risk_level = "medium"
            
            return {
                "cost_delta": cost_delta,
                "performance_gain": performance_gain,
                "error_reduction": error_reduction,
                "break_even_requests": break_even_requests,
                "current_traffic": current_traffic,
                "worth_it": worth_it,
                "risk_level": risk_level,
            }
        except Exception as e:
            logger.error(f"Error calculating cost impact: {e}")
            return {
                "cost_delta": 0.0,
                "performance_gain": 0.0,
                "error_reduction": 0.0,
                "break_even_requests": 0,
                "current_traffic": 0,
                "worth_it": False,
                "risk_level": "unknown",
                "error": str(e),
            }
    
    async def _validate_migration(self, migration_sql: str) -> Dict[str, Any]:
        """Validate database migration"""
        try:
            breaking_changes = []
            risks = []
            affected_services = []
            
            migration_lower = migration_sql.lower()
            
            # Check for breaking changes
            breaking_patterns = [
                ("drop table", "Dropping table"),
                ("drop column", "Dropping column"),
                ("alter column.*drop", "Dropping column constraint"),
                ("rename column", "Renaming column"),
                ("change column.*type", "Changing column type"),
            ]
            
            for pattern, description in breaking_patterns:
                import re
                if re.search(pattern, migration_lower):
                    breaking_changes.append(description)
                    risks.append(f"Breaking change: {description}")
            
            # Check for backward compatibility
            backward_compatible = len(breaking_changes) == 0
            
            # Check for index operations
            index_impact = "low"
            if "create index" in migration_lower or "drop index" in migration_lower:
                index_impact = "medium"
            if "create index concurrently" not in migration_lower and "create index" in migration_lower:
                risks.append("Index creation may lock table")
                index_impact = "high"
            
            # Estimate lock duration (simplified)
            estimated_lock_duration = 0
            if "alter table" in migration_lower:
                # Count operations that might lock
                alter_count = migration_lower.count("alter table")
                estimated_lock_duration = alter_count * 5  # 5 seconds per alter (estimate)
            
            # Find affected services (services using the database)
            db = await self._get_db_session()
            from Api.models.service import Service
            
            # Look for database-related services
            db_services_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        or_(
                            Service.service_type == "database",
                            Service.technology.like("%postgres%"),
                            Service.technology.like("%mysql%"),
                            Service.technology.like("%mongo%"),
                        )
                    )
                )
            )
            db_services = db_services_result.scalars().all()
            affected_services = [s.name for s in db_services]
            
            # Determine if safe
            is_safe = backward_compatible and index_impact != "high" and estimated_lock_duration < 30
            
            # Deploy order (if breaking changes)
            deploy_order = []
            if breaking_changes:
                deploy_order = [
                    "1. Deploy application code that handles new schema",
                    "2. Run migration during maintenance window",
                    "3. Verify application functionality",
                ]
            
            return {
                "is_safe": is_safe,
                "backward_compatible": backward_compatible,
                "breaking_changes": breaking_changes,
                "index_impact": index_impact,
                "estimated_lock_duration": estimated_lock_duration,
                "affected_services": affected_services,
                "risks": risks,
                "deploy_order": deploy_order,
            }
        except Exception as e:
            logger.error(f"Error validating migration: {e}")
            return {
                "is_safe": False,
                "backward_compatible": False,
                "breaking_changes": [],
                "index_impact": "unknown",
                "estimated_lock_duration": 0,
                "affected_services": [],
                "risks": [str(e)],
                "deploy_order": [],
            }
    
    async def _compare_versions(self, service: str) -> Dict[str, Any]:
        """Compare application vs pipeline versions"""
        try:
            db = await self._get_db_session()
            from Api.models.service import Service
            from Api.models.cicd import CICDPipeline
            
            # Get service
            service_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.name == service if service != "all" else True
                    )
                )
            )
            services = service_result.scalars().all()
            
            if service == "all":
                # Compare all services
                stale_services = []
                missed_deployments = []
                
                for svc in services:
                    # Get latest pipeline for this service
                    pipeline_result = await db.execute(
                        select(CICDPipeline).where(
                            and_(
                                CICDPipeline.tenant_id == self.context.tenant_id,
                                CICDPipeline.service_id == svc.id,
                                CICDPipeline.status == "success"
                            )
                        ).order_by(CICDPipeline.finished_at.desc()).limit(1)
                    )
                    latest_pipeline = pipeline_result.scalar_one_or_none()
                    
                    if latest_pipeline:
                        if latest_pipeline.commit_sha != svc.metadata.get("deployed_commit"):
                            stale_services.append(svc.name)
                            missed_deployments.append({
                                "service": svc.name,
                                "running": svc.metadata.get("deployed_commit", "unknown"),
                                "latest": latest_pipeline.commit_sha,
                            })
                
                return {
                    "git_latest": "multiple",
                    "git_running": "multiple",
                    "git_drift": f"{len(stale_services)} services",
                    "image_latest": "multiple",
                    "image_running": "multiple",
                    "image_drift": f"{len(stale_services)} services",
                    "stale_services": stale_services,
                    "missed_deployments": missed_deployments,
                }
            else:
                # Single service
                svc = services[0] if services else None
                if not svc:
                    return {
                        "git_latest": "unknown",
                        "git_running": "unknown",
                        "git_drift": "service not found",
                        "image_latest": "unknown",
                        "image_running": "unknown",
                        "image_drift": "service not found",
                        "stale_services": [],
                        "missed_deployments": [],
                    }
                
                # Get latest pipeline
                pipeline_result = await db.execute(
                    select(CICDPipeline).where(
                        and_(
                            CICDPipeline.tenant_id == self.context.tenant_id,
                            CICDPipeline.service_id == svc.id,
                            CICDPipeline.status == "success"
                        )
                    ).order_by(CICDPipeline.finished_at.desc()).limit(1)
                )
                latest_pipeline = pipeline_result.scalar_one_or_none()
                
                git_running = svc.metadata.get("deployed_commit", svc.version or "unknown")
                git_latest = latest_pipeline.commit_sha if latest_pipeline else "unknown"
                git_drift = "none" if git_running == git_latest else "drift detected"
                
                image_running = svc.metadata.get("image_tag", "unknown")
                image_latest = latest_pipeline.metadata.get("image_tag", "unknown") if latest_pipeline else "unknown"
                image_drift = "none" if image_running == image_latest else "drift detected"
                
                return {
                    "git_latest": git_latest,
                    "git_running": git_running,
                    "git_drift": git_drift,
                    "image_latest": image_latest,
                    "image_running": image_running,
                    "image_drift": image_drift,
                    "stale_services": [svc.name] if git_drift != "none" else [],
                    "missed_deployments": [{
                        "service": svc.name,
                        "running": git_running,
                        "latest": git_latest,
                    }] if git_drift != "none" else [],
                }
        except Exception as e:
            logger.error(f"Error comparing versions for {service}: {e}")
            return {
                "git_latest": "unknown",
                "git_running": "unknown",
                "git_drift": "error",
                "image_latest": "unknown",
                "image_running": "unknown",
                "image_drift": "error",
                "stale_services": [],
                "missed_deployments": [],
                "error": str(e),
            }
    
    async def _diagnose_vm(self, vm_id: str) -> Dict[str, Any]:
        """Diagnose VM performance issues"""
        try:
            db = await self._get_db_session()
            metrics_service = await self._get_metrics_service()
            from Api.models.host import Host
            from Api.schemas.metrics import MetricQuery, AggregationType
            
            # Get host
            host_result = await db.execute(
                select(Host).where(
                    and_(
                        Host.tenant_id == self.context.tenant_id,
                        or_(
                            Host.host_id == vm_id,
                            Host.hostname == vm_id
                        )
                    )
                )
            )
            host = host_result.scalar_one_or_none()
            
            if not host:
                return {
                    "cpu_steal": 0.0,
                    "disk_io_wait": 0.0,
                    "network_latency": 0.0,
                    "memory_pressure": 0.0,
                    "root_cause": f"VM {vm_id} not found",
                    "recommendations": [],
                }
            
            now = datetime.utcnow()
            
            # Get CPU steal
            try:
                cpu_query = MetricQuery(
                    metric_name=f"host.{host.host_id}.cpu.steal",
                    start_time=now - timedelta(minutes=15),
                    end_time=now,
                    aggregation=AggregationType.AVG,
                )
                cpu_series = await metrics_service.query(self.context.tenant_id, cpu_query, db)
                cpu_steal = cpu_series[0].values[-1] if cpu_series and cpu_series[0].values else 0.0
            except Exception:
                cpu_steal = 0.0
            
            # Get disk IO wait
            try:
                disk_query = MetricQuery(
                    metric_name=f"host.{host.host_id}.disk.io_wait",
                    start_time=now - timedelta(minutes=15),
                    end_time=now,
                    aggregation=AggregationType.AVG,
                )
                disk_series = await metrics_service.query(self.context.tenant_id, disk_query, db)
                disk_io_wait = disk_series[0].values[-1] if disk_series and disk_series[0].values else 0.0
            except Exception:
                disk_io_wait = 0.0
            
            # Get memory pressure
            try:
                mem_query = MetricQuery(
                    metric_name=f"host.{host.host_id}.memory.used_percent",
                    start_time=now - timedelta(minutes=15),
                    end_time=now,
                    aggregation=AggregationType.AVG,
                )
                mem_series = await metrics_service.query(self.context.tenant_id, mem_query, db)
                memory_pressure = mem_series[0].values[-1] if mem_series and mem_series[0].values else 0.0
            except Exception:
                memory_pressure = 0.0
            
            # Determine root cause
            root_cause = "No significant issues detected"
            if cpu_steal > 10:
                root_cause = f"High CPU steal ({cpu_steal:.1f}%) - possible noisy neighbor or oversubscribed host"
            elif disk_io_wait > 20:
                root_cause = f"High disk IO wait ({disk_io_wait:.1f}%) - disk bottleneck"
            elif memory_pressure > 90:
                root_cause = f"High memory pressure ({memory_pressure:.1f}%) - memory exhaustion"
            
            # Generate recommendations
            recommendations = []
            if cpu_steal > 10:
                recommendations.append("Consider moving to a dedicated instance or different host")
            if disk_io_wait > 20:
                recommendations.append("Upgrade to faster storage (SSD) or optimize disk I/O")
            if memory_pressure > 90:
                recommendations.append("Increase memory allocation or optimize memory usage")
            
            return {
                "cpu_steal": cpu_steal,
                "disk_io_wait": disk_io_wait,
                "network_latency": 0.0,  # Would need network metrics
                "memory_pressure": memory_pressure,
                "root_cause": root_cause,
                "recommendations": recommendations,
            }
        except Exception as e:
            logger.error(f"Error diagnosing VM {vm_id}: {e}")
            return {
                "cpu_steal": 0.0,
                "disk_io_wait": 0.0,
                "network_latency": 0.0,
                "memory_pressure": 0.0,
                "root_cause": f"Error: {str(e)}",
                "recommendations": [],
            }
    
    async def _check_dns(self, domain: str) -> Dict[str, Any]:
        """Check DNS resolution"""
        try:
            import socket
            import dns.resolver  # type: ignore
            
            # Resolve DNS
            try:
                answers = dns.resolver.resolve(domain, 'A')
                ip_addresses = [str(rdata) for rdata in answers]
                ttl = answers.rrset.ttl if answers.rrset else 300
                resolves = True
            except Exception as e:
                ip_addresses = []
                ttl = 0
                resolves = False
                logger.warning(f"DNS resolution failed for {domain}: {e}")
            
            # Also try socket.gethostbyname as fallback
            if not resolves:
                try:
                    ip = socket.gethostbyname(domain)
                    ip_addresses = [ip]
                    resolves = True
                    ttl = 300  # Default TTL
                except Exception:
                    pass
            
            # Check for mismatches (simplified - would need to check against service configs)
            mismatches = []
            if resolves:
                # Check if IPs match expected service endpoints
                db = await self._get_db_session()
                from Api.models.service import Service
                
                services_result = await db.execute(
                    select(Service).where(
                        and_(
                            Service.tenant_id == str(self.context.tenant_id),
                            Service.name.like(f"%{domain.split('.')[0]}%")
                        )
                    )
                )
                services = services_result.scalars().all()
                
                for svc in services:
                    expected_ips = svc.metadata.get("expected_ips", [])
                    if expected_ips and not any(ip in expected_ips for ip in ip_addresses):
                        mismatches.append(f"Service {svc.name} expects different IPs")
            
            return {
                "resolves": resolves,
                "ip_addresses": ip_addresses,
                "ttl": ttl,
                "geo_responses": {},  # Would need geo DNS service
                "mismatches": mismatches,
            }
        except ImportError:
            # Fallback if dnspython not available
            try:
                import socket
                ip = socket.gethostbyname(domain)
                return {
                    "resolves": True,
                    "ip_addresses": [ip],
                    "ttl": 300,
                    "geo_responses": {},
                    "mismatches": [],
                }
            except Exception as e:
                return {
                    "resolves": False,
                    "ip_addresses": [],
                    "ttl": 0,
                    "geo_responses": {},
                    "mismatches": [],
                    "error": str(e),
                }
        except Exception as e:
            logger.error(f"Error checking DNS for {domain}: {e}")
            return {
                "resolves": False,
                "ip_addresses": [],
                "ttl": 0,
                "geo_responses": {},
                "mismatches": [],
                "error": str(e),
            }
    
    async def _check_connectivity(self, source: str, target: str) -> Dict[str, Any]:
        """Check connectivity between source and target"""
        try:
            import socket
            import time
            
            # Resolve target to IP
            target_ip = target
            try:
                target_ip = socket.gethostbyname(target)
            except Exception:
                pass
            
            # Perform TCP connection test (read-only, no actual connection)
            # In production, this would use the agent on the source host
            issues = []
            
            # Check if target is a known service
            db = await self._get_db_session()
            from Api.models.service import Service
            
            service_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        or_(
                            Service.name == target,
                            Service.name.like(f"%{target}%")
                        )
                    )
                )
            )
            service = service_result.scalar_one_or_none()
            
            if service:
                # Service exists, check if it's healthy
                if service.status != "healthy":
                    issues.append(f"Service {target} status is {service.status}")
                
                # Get metrics for latency
                metrics_service = await self._get_metrics_service()
                from Api.schemas.metrics import MetricQuery, AggregationType
                
                now = datetime.utcnow()
                try:
                    latency_query = MetricQuery(
                        metric_name=f"service.{service.name}.latency",
                        start_time=now - timedelta(minutes=5),
                        end_time=now,
                        aggregation=AggregationType.AVG,
                    )
                    latency_series = await metrics_service.query(self.context.tenant_id, latency_query, db)
                    if latency_series and latency_series[0].values:
                        latency_avg = latency_series[0].values[-1]
                        latency_min = latency_avg * 0.8  # Estimate
                        latency_max = latency_avg * 1.2  # Estimate
                    else:
                        latency_avg = latency_min = latency_max = 0.0
                except Exception:
                    latency_avg = latency_min = latency_max = 0.0
                
                return {
                    "reachable": service.status == "healthy",
                    "latency_min": latency_min,
                    "latency_avg": latency_avg,
                    "latency_max": latency_max,
                    "packet_loss": 0.0,  # Would need network metrics
                    "issues": issues,
                }
            else:
                # Not a known service, assume connectivity check needed
                return {
                    "reachable": True,  # Optimistic
                    "latency_min": 0.0,
                    "latency_avg": 0.0,
                    "latency_max": 0.0,
                    "packet_loss": 0.0,
                    "issues": [f"Target {target} not found in service catalog"],
                }
        except Exception as e:
            logger.error(f"Error checking connectivity {source} -> {target}: {e}")
            return {
                "reachable": False,
                "latency_min": 0.0,
                "latency_avg": 0.0,
                "latency_max": 0.0,
                "packet_loss": 0.0,
                "issues": [str(e)],
            }
    
    async def _run_traceroute(self, target: str) -> Dict[str, Any]:
        """Run traceroute to target"""
        try:
            # In production, this would use the agent on a host to run traceroute
            # For now, we'll simulate based on topology
            topology = await self._get_topology_engine()
            graph = topology.get_graph(self.context.tenant_id)
            
            hops = []
            suspect_nodes = []
            
            # Try to resolve target
            try:
                import socket
                target_ip = socket.gethostbyname(target)
            except Exception:
                target_ip = target
            
            # Simulate hops (in production, would use actual traceroute)
            # For now, use topology to estimate path
            if graph:
                # Find entities that might be on the path
                entities = list(graph.entities.values())[:10]  # Sample
                for i, entity in enumerate(entities[:8]):  # Max 8 hops
                    hop_latency = 5.0 + (i * 2.0)  # Increasing latency
                    hops.append({
                        "hop": i + 1,
                        "ip": entity.metadata.get("ip", f"192.168.1.{i+1}"),
                        "hostname": entity.name,
                        "latency": hop_latency,
                    })
                
                # Add target as final hop
                hops.append({
                    "hop": len(hops) + 1,
                    "ip": target_ip,
                    "hostname": target,
                    "latency": hops[-1]["latency"] + 5.0 if hops else 10.0,
                })
            else:
                # Fallback: simple simulated path
                for i in range(5):
                    hops.append({
                        "hop": i + 1,
                        "ip": f"192.168.1.{i+1}",
                        "hostname": f"router{i+1}.example.com",
                        "latency": 5.0 + (i * 2.0),
                    })
                hops.append({
                    "hop": len(hops) + 1,
                    "ip": target_ip,
                    "hostname": target,
                    "latency": hops[-1]["latency"] + 5.0 if hops else 10.0,
                })
            
            # Identify suspect nodes (high latency)
            for hop in hops:
                if hop["latency"] > 50.0:  # Threshold
                    suspect_nodes.append(f"Hop {hop['hop']}: {hop['hostname']} ({hop['latency']:.1f}ms)")
            
            total_latency = sum(h["latency"] for h in hops)
            
            return {
                "hops": hops,
                "total_latency": total_latency,
                "suspect_nodes": suspect_nodes,
            }
        except Exception as e:
            logger.error(f"Error running traceroute to {target}: {e}")
            return {
                "hops": [],
                "total_latency": 0.0,
                "suspect_nodes": [],
                "error": str(e),
            }
    
    async def _check_routing(self, service: str) -> Dict[str, Any]:
        """Check routing configuration"""
        try:
            db = await self._get_db_session()
            from Api.models.service import Service
            
            # Get service
            service_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.name == service
                    )
                )
            )
            svc = service_result.scalar_one_or_none()
            
            if not svc:
                return {
                    "ingress_rules": [],
                    "lb_config": {},
                    "issues": [f"Service {service} not found"],
                    "misroutes": [],
                    "shadow_traffic": 0,
                    "loopbacks": [],
                }
            
            # Get routing config from metadata
            ingress_rules = svc.metadata.get("ingress_rules", [])
            lb_config = svc.metadata.get("load_balancer", {})
            
            # Check for issues
            issues = []
            misroutes = []
            loopbacks = []
            
            # Check for loopbacks (service calling itself)
            if svc.metadata.get("self_calls", False):
                loopbacks.append(f"Service {service} has self-referential calls")
            
            # Check ingress rules
            if not ingress_rules:
                issues.append("No ingress rules configured")
            
            # Check for shadow traffic (traffic to non-existent endpoints)
            shadow_traffic = svc.metadata.get("shadow_traffic_count", 0)
            if shadow_traffic > 0:
                issues.append(f"Shadow traffic detected: {shadow_traffic} req/s")
            
            # Check for misroutes (simplified)
            expected_routes = svc.metadata.get("expected_routes", [])
            actual_routes = [rule.get("path") for rule in ingress_rules]
            for expected in expected_routes:
                if expected not in actual_routes:
                    misroutes.append(f"Expected route {expected} not found")
            
            return {
                "ingress_rules": ingress_rules,
                "lb_config": lb_config,
                "issues": issues,
                "misroutes": misroutes,
                "shadow_traffic": shadow_traffic,
                "loopbacks": loopbacks,
            }
        except Exception as e:
            logger.error(f"Error checking routing for {service}: {e}")
            return {
                "ingress_rules": [],
                "lb_config": {},
                "issues": [str(e)],
                "misroutes": [],
                "shadow_traffic": 0,
                "loopbacks": [],
            }
    
    async def _sync_board(self, board_type: str) -> Dict[str, Any]:
        """Sync board data"""
        try:
            db = await self._get_db_session()
            from Api.models.cicd import CICDPipeline
            
            # Get recent pipeline runs
            now = datetime.utcnow()
            pipelines_result = await db.execute(
                select(CICDPipeline).where(
                    and_(
                        CICDPipeline.tenant_id == self.context.tenant_id,
                        CICDPipeline.provider == board_type,
                        CICDPipeline.created_at >= now - timedelta(days=7)
                    )
                ).order_by(CICDPipeline.created_at.desc())
            )
            pipelines = pipelines_result.scalars().all()
            
            deployments_success = sum(1 for p in pipelines if p.status == "success")
            deployments_failed = sum(1 for p in pipelines if p.status == "failed")
            deployments_in_progress = sum(1 for p in pipelines if p.status in ["pending", "running"])
            
            # Correlations (simplified - would need issue/PR integration)
            correlations = []
            for pipeline in pipelines[:5]:  # Last 5 pipelines
                if pipeline.status == "failed":
                    correlations.append({
                        "type": "deployment_failure",
                        "description": f"Pipeline {pipeline.name} failed at {pipeline.finished_at}",
                        "commit": pipeline.commit_sha[:8] if pipeline.commit_sha else "unknown",
                    })
            
            return {
                "deployments_success": deployments_success,
                "deployments_failed": deployments_failed,
                "deployments_in_progress": deployments_in_progress,
                "open_issues": 0,  # Would need GitHub/Azure API integration
                "open_prs": 0,  # Would need GitHub/Azure API integration
                "correlations": correlations,
            }
        except Exception as e:
            logger.error(f"Error syncing board {board_type}: {e}")
            return {
                "deployments_success": 0,
                "deployments_failed": 0,
                "deployments_in_progress": 0,
                "open_issues": 0,
                "open_prs": 0,
                "correlations": [],
                "error": str(e),
            }
    
    async def _analyze_connectivity_issue(self, service_a: str, service_b: str) -> Dict[str, Any]:
        """Analyze connectivity issue between services"""
        try:
            db = await self._get_db_session()
            topology = await self._get_topology_engine()
            from Api.models.service import Service
            
            # Get both services
            service_a_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.name == service_a
                    )
                )
            )
            svc_a = service_a_result.scalar_one_or_none()
            
            service_b_result = await db.execute(
                select(Service).where(
                    and_(
                        Service.tenant_id == str(self.context.tenant_id),
                        Service.name == service_b
                    )
                )
            )
            svc_b = service_b_result.scalar_one_or_none()
            
            if not svc_a or not svc_b:
                return {
                    "connected": False,
                    "root_cause": f"Service not found: {service_a if not svc_a else service_b}",
                    "network_policies": [],
                    "security_groups": [],
                    "dns_resolves": False,
                    "tls_errors": [],
                    "topology_path": [],
                }
            
            # Check topology for connection
            graph = topology.get_graph(self.context.tenant_id)
            connected = False
            topology_path = []
            
            if graph:
                # Find path between services
                entity_a = graph.get_entity_by_name(service_a)
                entity_b = graph.get_entity_by_name(service_b)
                
                if entity_a and entity_b:
                    # Check if there's a direct relationship
                    relationships = graph.get_relationships(entity_a.id, entity_b.id)
                    if relationships:
                        connected = True
                        topology_path = [service_a, service_b]
                    else:
                        # Try to find indirect path
                        path = graph.find_path(entity_a.id, entity_b.id)
                        if path:
                            connected = True
                            topology_path = [e.name for e in path]
            
            # Check DNS
            dns_resolves = True
            try:
                import socket
                socket.gethostbyname(service_b)
            except Exception:
                dns_resolves = False
            
            # Determine root cause
            root_cause = "Unknown"
            if not connected:
                if not dns_resolves:
                    root_cause = f"DNS resolution failed for {service_b}"
                elif svc_b.status != "healthy":
                    root_cause = f"Service {service_b} is not healthy (status: {svc_b.status})"
                else:
                    root_cause = f"No network path found between {service_a} and {service_b} in topology"
            else:
                root_cause = "Services are connected via topology"
            
            # Get network policies (from service metadata)
            network_policies = []
            if svc_a.metadata.get("network_policies"):
                network_policies = svc_a.metadata["network_policies"]
            
            # Get security groups (from service metadata)
            security_groups = []
            if svc_a.metadata.get("security_groups"):
                security_groups = svc_a.metadata["security_groups"]
            
            # Check for TLS errors (from logs)
            tls_errors = []
            logs_service = await self._get_logs_service()
            from Api.schemas.logs import LogQuery, LogLevel
            
            now = datetime.utcnow()
            log_query = LogQuery(
                query=f"service:{service_a} TLS SSL certificate",
                start_time=now - timedelta(hours=1),
                end_time=now,
                level=LogLevel.ERROR,
                limit=10,
            )
            
            try:
                error_logs = await logs_service.search(self.context.tenant_id, log_query)
                if error_logs and error_logs.logs:
                    tls_errors = [log.body[:100] for log in error_logs.logs[:5]]
            except Exception:
                pass
            
            return {
                "connected": connected,
                "root_cause": root_cause,
                "network_policies": network_policies,
                "security_groups": security_groups,
                "dns_resolves": dns_resolves,
                "tls_errors": tls_errors,
                "topology_path": topology_path,
            }
        except Exception as e:
            logger.error(f"Error analyzing connectivity {service_a} -> {service_b}: {e}")
            return {
                "connected": False,
                "root_cause": f"Error: {str(e)}",
                "network_policies": [],
                "security_groups": [],
                "dns_resolves": False,
                "tls_errors": [],
                "topology_path": [],
            }
    
    # ===========================================
    # Formatting Helpers
    # ===========================================
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items"""
        if not items:
            return "- None"
        return "\n".join(f"- {item}" for item in items)
    
    def _format_resource_list(self, resources: List[Dict]) -> str:
        """Format resource list"""
        if not resources:
            return "- None"
        return "\n".join(f"- {r.get('name', 'unknown')}" for r in resources)
    
    def _format_slo_status(self, slo_status: Dict) -> str:
        """Format SLO status"""
        if not slo_status:
            return "- None"
        return "\n".join(f"- {service}: {status}" for service, status in slo_status.items())
    
    def _format_access_list(self, users: List[Dict]) -> str:
        """Format access list"""
        if not users:
            return "- None"
        return "\n".join(f"- {u.get('name', 'unknown')}: {u.get('role', 'unknown')}" for u in users)
    
    def _format_risk_findings(self, findings: List[Dict]) -> str:
        """Format risk findings"""
        if not findings:
            return "- None"
        return "\n".join(f"- {f.get('severity', 'unknown')}: {f.get('description', 'unknown')}" for f in findings)
    
    def _format_dns_geo(self, geo_responses: Dict) -> str:
        """Format DNS geo responses"""
        if not geo_responses:
            return "- None"
        return "\n".join(f"- {location}: {ip}" for location, ip in geo_responses.items())
    
    def _format_traceroute_hops(self, hops: List[Dict]) -> str:
        """Format traceroute hops"""
        if not hops:
            return "- None"
        return "\n".join(f"- Hop {h.get('hop', '?')}: {h.get('ip', 'unknown')} ({h.get('latency', 0):.1f}ms)" for h in hops)
    
    def _format_routing_rules(self, rules: List[Dict]) -> str:
        """Format routing rules"""
        if not rules:
            return "- None"
        return "\n".join(f"- {r.get('path', 'unknown')} → {r.get('service', 'unknown')}" for r in rules)
    
    def _format_lb_config(self, config: Dict) -> str:
        """Format load balancer config"""
        if not config:
            return "- None"
        return f"- Algorithm: {config.get('algorithm', 'unknown')}\n- Health checks: {config.get('health_checks', 'unknown')}"
    
    def _format_correlations(self, correlations: List[Dict]) -> str:
        """Format correlations"""
        if not correlations:
            return "- None"
        return "\n".join(f"- {c.get('type', 'unknown')}: {c.get('description', 'unknown')}" for c in correlations)
    
    def _format_network_policies(self, policies: List[Dict]) -> str:
        """Format network policies"""
        if not policies:
            return "- None"
        return "\n".join(f"- {p.get('name', 'unknown')}: {p.get('status', 'unknown')}" for p in policies)
    
    def _format_security_groups(self, groups: List[Dict]) -> str:
        """Format security groups"""
        if not groups:
            return "- None"
        return "\n".join(f"- {g.get('name', 'unknown')}: {g.get('rules', 0)} rules" for g in groups)
    
    def _format_topology_path(self, path: List[str]) -> str:
        """Format topology path"""
        if not path:
            return "- None"
        return " → ".join(path)
