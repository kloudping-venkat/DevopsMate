"""
Flare collection - collect diagnostic information.
Similar to Datadog's agent flare command.
"""

import tarfile
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def collect_flare(output_path: Optional[str] = None, include_sensitive: bool = False) -> str:
    """
    Collect diagnostic information into a tarball.
    
    Similar to Datadog's agent flare:
    - Agent logs
    - Configuration files (with optional sensitive data removal)
    - System information
    - Component status
    - Component-specific flare data
    
    Args:
        output_path: Output file path
        include_sensitive: Include sensitive data (API keys, etc.)
        
    Returns:
        Path to created flare file
    """
    if not output_path:
        import time
        output_path = f"devopsmate-agent-flare-{int(time.time())}.tar.gz"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        flare_dir = Path(tmpdir) / "flare"
        flare_dir.mkdir()
        
        # Collect logs
        log_dir = flare_dir / "logs"
        log_dir.mkdir()
        _collect_logs(log_dir)
        
        # Collect config (with sensitive data handling)
        config_dir = flare_dir / "config"
        config_dir.mkdir()
        _collect_config(config_dir, include_sensitive)
        
        # Collect system info
        system_file = flare_dir / "system_info.txt"
        _collect_system_info(system_file)
        
        # Collect agent status
        status_file = flare_dir / "agent_status.json"
        _collect_agent_status(status_file)
        
        # Collect component-specific flare data
        components_dir = flare_dir / "components"
        components_dir.mkdir()
        _collect_component_flare(components_dir)
        
        # Collect network info
        network_file = flare_dir / "network_info.txt"
        _collect_network_info(network_file)
        
        # Create tarball
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(flare_dir, arcname="flare")
        
        logger.info(f"Flare collected: {output_path}")
        return output_path


def _collect_logs(log_dir: Path):
    """Collect agent logs."""
    log_paths = [
        Path("/var/log/devopsmate-agent.log"),
        Path.home() / ".devopsmate" / "agent.log",
        Path("agent.log"),
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            shutil.copy2(log_path, log_dir / log_path.name)
            break


def _collect_config(config_dir: Path, include_sensitive: bool = False):
    """Collect configuration files."""
    config_paths = [
        Path("agent.yaml"),
        Path("/etc/devopsmate/agent.yaml"),
        Path.home() / ".devopsmate" / "agent.yaml",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            if include_sensitive:
                shutil.copy2(config_path, config_dir / config_path.name)
            else:
                # Remove sensitive data
                content = config_path.read_text()
                # Remove API keys, tokens, etc.
                import re
                content = re.sub(r'api_key:\s*["\']?[^"\'\n]+["\']?', 'api_key: "***REDACTED***"', content)
                content = re.sub(r'api-key:\s*["\']?[^"\'\n]+["\']?', 'api-key: "***REDACTED***"', content)
                content = re.sub(r'token:\s*["\']?[^"\'\n]+["\']?', 'token: "***REDACTED***"', content)
                (config_dir / config_path.name).write_text(content)
            break


def _collect_system_info(output_file: Path):
    """Collect system information."""
    import platform
    import sys
    
    info = f"""System Information
==================
Platform: {platform.platform()}
System: {platform.system()}
Release: {platform.release()}
Version: {platform.version()}
Machine: {platform.machine()}
Processor: {platform.processor()}
Python: {sys.version}
"""
    
    output_file.write_text(info)


def _collect_agent_status(output_file: Path):
    """Collect agent status."""
    from agent.internal.status.status import get_agent_status
    import json
    
    status = get_agent_status(detailed=True)
    output_file.write_text(json.dumps(status, indent=2, default=str))


def _collect_component_flare(components_dir: Path):
    """Collect component-specific flare data."""
    # This would collect data from each component
    # For now, create placeholder files
    
    components = ["discovery", "collectors", "forwarder"]
    
    for comp_name in components:
        comp_file = components_dir / f"{comp_name}.json"
        comp_file.write_text(json.dumps({
            "component": comp_name,
            "status": "unknown",
            "note": "Component flare data collection not yet implemented"
        }, indent=2))


def _collect_network_info(output_file: Path):
    """Collect network information."""
    import socket
    import platform
    
    info = []
    info.append("Network Information")
    info.append("=" * 50)
    info.append(f"Hostname: {socket.gethostname()}")
    info.append(f"FQDN: {socket.getfqdn()}")
    
    try:
        # Get IP addresses
        hostname = socket.gethostname()
        ip_addrs = socket.gethostbyname_ex(hostname)[2]
        info.append(f"\nIP Addresses:")
        for ip in ip_addrs:
            info.append(f"  - {ip}")
    except Exception as e:
        info.append(f"\nError getting IP addresses: {e}")
    
    output_file.write_text("\n".join(info))
