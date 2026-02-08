"""Agent configuration management."""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AgentConfig:
    """Configuration for the DevopsMate Universal Agent."""
    
    # Connection settings
    endpoint: str = "http://localhost:8000/api/v1/ingest"
    api_key: str = ""
    tenant_id: str = ""
    
    # Collection settings
    collect_host_metrics: bool = True
    collect_container_metrics: bool = True
    collect_logs: bool = True
    collect_network: bool = True
    collect_traces: bool = True
    
    # Intervals (seconds)
    host_metrics_interval: int = 15
    container_metrics_interval: int = 15
    log_collection_interval: int = 5
    network_metrics_interval: int = 30
    discovery_interval: int = 60
    flush_interval: int = 10
    
    # Auto-instrumentation
    auto_instrument: bool = True
    instrument_java: bool = True
    instrument_python: bool = True
    instrument_nodejs: bool = True
    instrument_dotnet: bool = True
    instrument_go: bool = True
    
    # Log collection
    log_paths: List[str] = field(default_factory=lambda: [
        "/var/log/*.log",
        "/var/log/**/*.log",
    ])
    log_exclude_patterns: List[str] = field(default_factory=lambda: [
        "*.gz",
        "*.tar",
        "*.zip",
    ])
    
    # Process discovery
    process_discovery_enabled: bool = True
    process_exclude_patterns: List[str] = field(default_factory=lambda: [
        "^\\[.*\\]$",  # Kernel threads
    ])
    
    # Container settings
    docker_socket: str = "/var/run/docker.sock"
    containerd_socket: str = "/run/containerd/containerd.sock"
    kubernetes_enabled: bool = True
    
    # Network settings
    capture_network_flows: bool = True
    network_sample_rate: float = 0.1  # 10% sampling
    
    # Buffer settings
    buffer_size: int = 10000
    max_batch_size: int = 1000
    
    # Resource limits
    max_cpu_percent: float = 5.0
    max_memory_mb: int = 256
    
    # TLS settings
    tls_enabled: bool = True
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    tls_ca_path: Optional[str] = None
    tls_skip_verify: bool = False
    
    # Tags to add to all data
    global_tags: Dict[str, str] = field(default_factory=dict)
    
    # Host identification
    host_id: Optional[str] = None
    host_name: Optional[str] = None
    
    # Forwarder settings
    failover_endpoints: List[Dict[str, Any]] = field(default_factory=list)  # Failover endpoints
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config from environment variables."""
        return cls(
            endpoint=os.getenv("DM_ENDPOINT", "http://localhost:8000/api/v1/ingest"),
            api_key=os.getenv("DM_API_KEY", ""),
            tenant_id=os.getenv("DM_TENANT_ID", ""),
            collect_host_metrics=os.getenv("DM_COLLECT_HOST_METRICS", "true").lower() == "true",
            collect_container_metrics=os.getenv("DM_COLLECT_CONTAINER_METRICS", "true").lower() == "true",
            collect_logs=os.getenv("DM_COLLECT_LOGS", "true").lower() == "true",
            collect_network=os.getenv("DM_COLLECT_NETWORK", "true").lower() == "true",
            auto_instrument=os.getenv("DM_AUTO_INSTRUMENT", "true").lower() == "true",
            host_metrics_interval=int(os.getenv("DM_HOST_METRICS_INTERVAL", "15")),
            discovery_interval=int(os.getenv("DM_DISCOVERY_INTERVAL", "60")),
            buffer_size=int(os.getenv("DM_BUFFER_SIZE", "10000")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "endpoint": self.endpoint,
            "tenant_id": self.tenant_id,
            "collect_host_metrics": self.collect_host_metrics,
            "collect_container_metrics": self.collect_container_metrics,
            "collect_logs": self.collect_logs,
            "collect_network": self.collect_network,
            "auto_instrument": self.auto_instrument,
            "host_metrics_interval": self.host_metrics_interval,
            "discovery_interval": self.discovery_interval,
        }
