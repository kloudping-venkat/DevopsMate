"""
Health checking for agent components.
Similar to Datadog's health check system.
"""

from typing import Dict, Any, List
from agent.internal.status.status import get_agent_status


def check_health() -> Dict[str, Any]:
    """
    Check agent health.
    
    Returns:
        Dict with 'healthy' bool and 'errors' list
    """
    status = get_agent_status()
    
    healthy = True
    errors = []
    
    # Check if agent is running
    if status.get("status") != "running":
        healthy = False
        errors.append("Agent is not running")
    
    # Check components
    components = status.get("components", {})
    for comp_name, comp_status in components.items():
        if not comp_status.get("healthy", False):
            healthy = False
            errors.append(f"Component {comp_name} is unhealthy")
    
    return {
        "healthy": healthy,
        "errors": errors,
        "status": status,
    }
