"""
Configuration validator - validates agent configuration.
"""

from typing import List
from agent.pkg.config.loader import AgentConfig


def validate_config(config: AgentConfig) -> List[str]:
    """
    Validate agent configuration.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    if not config.endpoint:
        errors.append("endpoint is required")
    
    if not config.api_key:
        errors.append("api_key is required")
    
    if not config.tenant_id:
        errors.append("tenant_id is required")
    
    # Validate endpoint URL
    if config.endpoint:
        if not (config.endpoint.startswith("http://") or config.endpoint.startswith("https://")):
            errors.append("endpoint must be a valid HTTP/HTTPS URL")
    
    # Validate intervals
    if config.host_metrics_interval < 1:
        errors.append("host_metrics_interval must be >= 1 second")
    
    if config.container_metrics_interval < 1:
        errors.append("container_metrics_interval must be >= 1 second")
    
    if config.flush_interval < 1:
        errors.append("flush_interval must be >= 1 second")
    
    # Validate buffer size
    if config.buffer_size < 100:
        errors.append("buffer_size must be >= 100")
    
    if config.max_batch_size > config.buffer_size:
        errors.append("max_batch_size cannot exceed buffer_size")
    
    # Validate resource limits
    if config.max_cpu_percent < 0 or config.max_cpu_percent > 100:
        errors.append("max_cpu_percent must be between 0 and 100")
    
    if config.max_memory_mb < 64:
        errors.append("max_memory_mb must be >= 64 MB")
    
    return errors
