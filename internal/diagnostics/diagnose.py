"""
Comprehensive diagnostics system.
Similar to Datadog's diagnose command.
"""

import sys
import platform
import socket
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def run_diagnostics() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Run comprehensive diagnostics.
    
    Returns:
        Dict with category -> check_name -> result
    """
    results = {}
    
    # System checks
    results['System'] = _check_system()
    
    # Configuration checks
    results['Configuration'] = _check_configuration()
    
    # Network checks
    results['Network'] = _check_network()
    
    # File system checks
    results['File System'] = _check_filesystem()
    
    # Component checks
    results['Components'] = _check_components()
    
    return results


def _check_system() -> Dict[str, Dict[str, Any]]:
    """Check system-level diagnostics."""
    checks = {}
    
    # Python version
    checks['Python Version'] = {
        'status': 'ok',
        'message': f"{sys.version.split()[0]}",
    }
    
    # Platform
    checks['Platform'] = {
        'status': 'ok',
        'message': f"{platform.system()} {platform.release()}",
    }
    
    # Hostname resolution
    try:
        hostname = socket.gethostname()
        socket.gethostbyname(hostname)
        checks['Hostname Resolution'] = {
            'status': 'ok',
            'message': f"Hostname '{hostname}' resolves correctly",
        }
    except Exception as e:
        checks['Hostname Resolution'] = {
            'status': 'error',
            'message': f"Failed to resolve hostname: {e}",
            'errors': [str(e)],
        }
    
    return checks


def _check_configuration() -> Dict[str, Dict[str, Any]]:
    """Check configuration diagnostics."""
    checks = {}
    
    # Config file locations
    config_paths = [
        Path("agent.yaml"),
        Path("/etc/devopsmate/agent.yaml"),
        Path.home() / ".devopsmate" / "agent.yaml",
    ]
    
    found_config = None
    for path in config_paths:
        if path.exists():
            found_config = path
            break
    
    if found_config:
        checks['Config File'] = {
            'status': 'ok',
            'message': f"Found config at: {found_config}",
        }
        
        # Try to load and validate
        try:
            from agent.pkg.config.loader import load_config
            from agent.pkg.config.validator import validate_config
            
            config = load_config(str(found_config))
            errors = validate_config(config)
            
            if errors:
                checks['Config Validation'] = {
                    'status': 'error',
                    'message': f"Config has {len(errors)} errors",
                    'errors': errors,
                }
            else:
                checks['Config Validation'] = {
                    'status': 'ok',
                    'message': "Config is valid",
                }
        except Exception as e:
            checks['Config Validation'] = {
                'status': 'error',
                'message': f"Failed to load config: {e}",
                'errors': [str(e)],
            }
    else:
        checks['Config File'] = {
            'status': 'warning',
            'message': "No config file found in standard locations",
        }
    
    return checks


def _check_network() -> Dict[str, Dict[str, Any]]:
    """Check network diagnostics."""
    checks = {}
    
    # DNS resolution
    try:
        socket.gethostbyname('google.com')
        checks['DNS Resolution'] = {
            'status': 'ok',
            'message': "DNS resolution working",
        }
    except Exception as e:
        checks['DNS Resolution'] = {
            'status': 'error',
            'message': f"DNS resolution failed: {e}",
            'errors': [str(e)],
        }
    
    # Connectivity to common endpoints
    endpoints = [
        ('8.8.8.8', 53),  # Google DNS
    ]
    
    connectivity_ok = True
    for host, port in endpoints:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result != 0:
                connectivity_ok = False
        except Exception:
            connectivity_ok = False
    
    checks['Network Connectivity'] = {
        'status': 'ok' if connectivity_ok else 'warning',
        'message': "Network connectivity test" + (" passed" if connectivity_ok else " failed"),
    }
    
    return checks


def _check_filesystem() -> Dict[str, Dict[str, Any]]:
    """Check filesystem diagnostics."""
    checks = {}
    
    # Check required directories
    required_dirs = [
        Path("/tmp"),
        Path("/var/log"),
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing_dirs.append(str(dir_path))
    
    if missing_dirs:
        checks['Required Directories'] = {
            'status': 'warning',
            'message': f"Missing directories: {', '.join(missing_dirs)}",
        }
    else:
        checks['Required Directories'] = {
            'status': 'ok',
            'message': "All required directories exist",
        }
    
    # Check write permissions
    try:
        test_file = Path("/tmp") / "devopsmate_test_write"
        test_file.write_text("test")
        test_file.unlink()
        checks['Write Permissions'] = {
            'status': 'ok',
            'message': "Write permissions OK",
        }
    except Exception as e:
        checks['Write Permissions'] = {
            'status': 'error',
            'message': f"Write permission test failed: {e}",
            'errors': [str(e)],
        }
    
    return checks


def _check_components() -> Dict[str, Dict[str, Any]]:
    """Check component diagnostics."""
    checks = {}
    
    # Check if components can be imported
    components = [
        ('CollectorManager', 'agent.internal.core.collector_manager'),
        ('Forwarder', 'agent.internal.core.forwarder'),
        ('DiscoveryManager', 'agent.internal.discovery.manager'),
    ]
    
    for comp_name, module_path in components:
        try:
            __import__(module_path)
            checks[comp_name] = {
                'status': 'ok',
                'message': "Component can be imported",
            }
        except Exception as e:
            checks[comp_name] = {
                'status': 'error',
                'message': f"Failed to import: {e}",
                'errors': [str(e)],
            }
    
    return checks
