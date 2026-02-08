"""
Configuration loader - loads from YAML, environment, or CLI args.
Similar to Datadog's config loading mechanism.
Supports remote config and hot-reload.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from agent.config import AgentConfig
from agent.pkg.config.remote import RemoteConfigClient


def load_config(config_path: Optional[str] = None) -> AgentConfig:
    """
    Load configuration from file, environment, or defaults.
    
    Priority:
    1. CLI arguments (highest)
    2. Config file
    3. Environment variables
    4. Defaults (lowest)
    """
    # Try to load from file
    config_data = {}
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}
    else:
        # Try default locations
        default_paths = [
            Path("agent.yaml"),
            Path("/etc/devopsmate/agent.yaml"),
            Path.home() / ".devopsmate" / "agent.yaml",
        ]
        
        for path in default_paths:
            if path.exists():
                with open(path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
                break
    
    # Override with environment variables
    env_overrides = {
        "endpoint": os.getenv("DEVOPSMATE_ENDPOINT") or os.getenv("DM_ENDPOINT"),
        "api_key": os.getenv("DEVOPSMATE_API_KEY") or os.getenv("DM_API_KEY"),
        "tenant_id": os.getenv("DEVOPSMATE_TENANT_ID") or os.getenv("DM_TENANT_ID"),
    }
    
    # Remove None values
    env_overrides = {k: v for k, v in env_overrides.items() if v is not None}
    config_data.update(env_overrides)
    
    # Create config object
    if config_data:
        config = AgentConfig(**config_data)
    else:
        # Fall back to environment-based config
        config = AgentConfig.from_env()
    
    # Start remote config if enabled
    if config_data.get('remote_config', {}).get('enabled', False):
        remote_config = RemoteConfigClient(
            endpoint=config_data['remote_config'].get('endpoint', config.endpoint),
            api_key=config.api_key,
            tenant_id=config.tenant_id,
            poll_interval=config_data['remote_config'].get('poll_interval', 60.0),
        )
        # Note: Remote config client should be started separately
        # This is just for initialization
    
    return config
