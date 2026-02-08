"""
Agent status reporting.
Similar to Datadog's status command.
"""

import os
import json
import time
import platform
from pathlib import Path
from typing import Dict, Any, Optional


def get_agent_status(detailed: bool = False) -> Dict[str, Any]:
    """
    Get current agent status.
    
    Similar to Datadog's agent status command.
    
    Args:
        detailed: If True, include detailed component status
        
    Returns:
        Dict with agent status information
    """
    # Check if agent is running (check PID file or process)
    pid_file = Path("/var/run/devopsmate-agent.pid")
    pid_file_alt = Path.home() / ".devopsmate" / "agent.pid"
    
    status = {
        "version": "1.0.0",
        "status": "unknown",
        "pid": None,
        "uptime": "unknown",
        "platform": f"{platform.system()} {platform.release()}",
        "python_version": platform.python_version(),
        "components": {},
    }
    
    # Try to read PID file
    pid = None
    for pid_path in [pid_file, pid_file_alt]:
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                status["pid"] = pid
                status["status"] = "running"
                
                # Check if process is actually running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    
                    # Try to get uptime from process start time
                    if detailed:
                        try:
                            import psutil
                            proc = psutil.Process(pid)
                            uptime_seconds = time.time() - proc.create_time()
                            status["uptime"] = _format_uptime(uptime_seconds)
                        except:
                            pass
                except OSError:
                    status["status"] = "stopped"
                break
            except Exception:
                pass
    
    # Get component status if detailed
    if detailed:
        status["components"] = _get_component_status()
    
    return status


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "<1m"


def _get_component_status() -> Dict[str, Any]:
    """Get status of all components."""
    components = {}
    
    # Try to get component status from running agent
    # This would typically come from the agent's ComponentManager
    # For now, return basic structure
    
    component_names = [
        "discovery",
        "collectors",
        "forwarder",
    ]
    
    for comp_name in component_names:
        components[comp_name] = {
            "status": "unknown",
            "running": False,
        }
    
    return components


def format_status(status: Dict[str, Any], format: str = "text") -> str:
    """
    Format status output.
    
    Args:
        status: Status dict
        format: Output format (text, json)
        
    Returns:
        Formatted status string
    """
    if format == "json":
        return json.dumps(status, indent=2)
    
    # Text format
    lines = []
    lines.append("=== DevopsMate Agent Status ===")
    lines.append(f"Version: {status.get('version', 'unknown')}")
    lines.append(f"Status: {status.get('status', 'unknown')}")
    lines.append(f"PID: {status.get('pid', 'N/A')}")
    lines.append(f"Uptime: {status.get('uptime', 'unknown')}")
    lines.append(f"Platform: {status.get('platform', 'unknown')}")
    lines.append(f"Python: {status.get('python_version', 'unknown')}")
    
    if status.get('components'):
        lines.append("\nComponents:")
        for comp_name, comp_status in status['components'].items():
            status_icon = "✓" if comp_status.get('running') else "✗"
            lines.append(f"  {status_icon} {comp_name}: {comp_status.get('status', 'unknown')}")
    
    return "\n".join(lines)
