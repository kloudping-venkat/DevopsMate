"""Container metrics collector for Docker and Kubernetes."""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.config import AgentConfig
from agent.buffer import DataBuffer

logger = logging.getLogger(__name__)


class ContainerMetricsCollector:
    """
    Collects container metrics from:
    - Docker daemon
    - Containerd
    - Kubernetes (via cgroup stats)
    
    Metrics collected:
    - CPU usage
    - Memory usage
    - Network I/O
    - Block I/O
    - Container state
    """
    
    def __init__(self, config: AgentConfig, buffer: DataBuffer):
        self.config = config
        self.buffer = buffer
        self.interval = config.container_metrics_interval
        self.last_count = 0
        
        # Container runtime detection
        self.docker_available = Path(config.docker_socket).exists()
        self.containerd_available = Path(config.containerd_socket).exists()
        self.kubernetes_available = config.kubernetes_enabled and self._detect_kubernetes()
        
        # Cache for container info
        self._container_cache: Dict[str, Dict] = {}
        
        logger.info(f"Container collector initialized: docker={self.docker_available}, k8s={self.kubernetes_available}")
    
    def _detect_kubernetes(self) -> bool:
        """Detect if running in Kubernetes."""
        return (
            os.environ.get("KUBERNETES_SERVICE_HOST") is not None or
            Path("/var/run/secrets/kubernetes.io").exists()
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect container metrics."""
        metrics = []
        now = datetime.utcnow()
        
        # Collect from Docker
        if self.docker_available:
            docker_metrics = await self._collect_docker_metrics(now)
            metrics.extend(docker_metrics)
        
        # Collect from cgroups (works for Docker, containerd, K8s)
        cgroup_metrics = await self._collect_cgroup_metrics(now)
        metrics.extend(cgroup_metrics)
        
        # Add Kubernetes metadata if available
        if self.kubernetes_available:
            metrics = self._enrich_with_k8s_metadata(metrics)
        
        # Add to buffer
        await self.buffer.add_batch("metrics", metrics)
        self.last_count = len(metrics)
        
        return metrics
    
    async def _collect_docker_metrics(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect metrics from Docker daemon."""
        metrics = []
        
        try:
            # Use Docker SDK if available
            import docker
            client = docker.from_env()
            
            for container in client.containers.list():
                stats = container.stats(stream=False)
                
                container_id = container.id[:12]
                container_name = container.name
                image = container.image.tags[0] if container.image.tags else "unknown"
                
                base_tags = {
                    "container_id": container_id,
                    "container_name": container_name,
                    "image": image,
                    **self.config.global_tags,
                }
                
                # CPU metrics
                cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                           stats["precpu_stats"]["cpu_usage"]["total_usage"]
                system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                              stats["precpu_stats"]["system_cpu_usage"]
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1])) * 100
                else:
                    cpu_percent = 0
                
                metrics.append({
                    "metric": "container.cpu.usage",
                    "value": cpu_percent,
                    "timestamp": timestamp.isoformat(),
                    "tags": base_tags,
                    "unit": "percent",
                })
                
                # Memory metrics
                mem_usage = stats["memory_stats"].get("usage", 0)
                mem_limit = stats["memory_stats"].get("limit", 0)
                
                metrics.extend([
                    {
                        "metric": "container.memory.usage",
                        "value": mem_usage,
                        "timestamp": timestamp.isoformat(),
                        "tags": base_tags,
                        "unit": "bytes",
                    },
                    {
                        "metric": "container.memory.limit",
                        "value": mem_limit,
                        "timestamp": timestamp.isoformat(),
                        "tags": base_tags,
                        "unit": "bytes",
                    },
                ])
                
                if mem_limit > 0:
                    metrics.append({
                        "metric": "container.memory.percent",
                        "value": (mem_usage / mem_limit) * 100,
                        "timestamp": timestamp.isoformat(),
                        "tags": base_tags,
                        "unit": "percent",
                    })
                
                # Network metrics
                networks = stats.get("networks", {})
                for network_name, network_stats in networks.items():
                    net_tags = {**base_tags, "network": network_name}
                    
                    metrics.extend([
                        {
                            "metric": "container.network.rx_bytes",
                            "value": network_stats.get("rx_bytes", 0),
                            "timestamp": timestamp.isoformat(),
                            "tags": net_tags,
                            "unit": "bytes",
                        },
                        {
                            "metric": "container.network.tx_bytes",
                            "value": network_stats.get("tx_bytes", 0),
                            "timestamp": timestamp.isoformat(),
                            "tags": net_tags,
                            "unit": "bytes",
                        },
                    ])
                
                # Block I/O
                blkio = stats.get("blkio_stats", {}).get("io_service_bytes_recursive", [])
                for io_stat in blkio or []:
                    op = io_stat.get("op", "").lower()
                    if op in ["read", "write"]:
                        metrics.append({
                            "metric": f"container.blkio.{op}_bytes",
                            "value": io_stat.get("value", 0),
                            "timestamp": timestamp.isoformat(),
                            "tags": base_tags,
                            "unit": "bytes",
                        })
                
        except ImportError:
            logger.debug("Docker SDK not available, using cgroup fallback")
        except Exception as e:
            logger.error(f"Docker metrics collection failed: {e}")
        
        return metrics
    
    async def _collect_cgroup_metrics(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect metrics from cgroups (Linux only)."""
        metrics = []
        
        # Check cgroup version
        cgroup_v2 = Path("/sys/fs/cgroup/cgroup.controllers").exists()
        
        if cgroup_v2:
            metrics = await self._collect_cgroup_v2_metrics(timestamp)
        else:
            metrics = await self._collect_cgroup_v1_metrics(timestamp)
        
        return metrics
    
    async def _collect_cgroup_v2_metrics(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect metrics from cgroup v2."""
        metrics = []
        cgroup_root = Path("/sys/fs/cgroup")
        
        if not cgroup_root.exists():
            return metrics
        
        # Find container cgroups
        for cgroup_path in cgroup_root.glob("**/cgroup.procs"):
            cgroup_dir = cgroup_path.parent
            
            # Skip non-container cgroups
            if not self._is_container_cgroup(cgroup_dir):
                continue
            
            container_id = self._extract_container_id(cgroup_dir)
            if not container_id:
                continue
            
            base_tags = {
                "container_id": container_id,
                **self.config.global_tags,
            }
            
            # CPU metrics
            cpu_stat = cgroup_dir / "cpu.stat"
            if cpu_stat.exists():
                stats = self._parse_stat_file(cpu_stat)
                if "usage_usec" in stats:
                    metrics.append({
                        "metric": "container.cpu.usage_usec",
                        "value": stats["usage_usec"],
                        "timestamp": timestamp.isoformat(),
                        "tags": base_tags,
                    })
            
            # Memory metrics
            memory_current = cgroup_dir / "memory.current"
            if memory_current.exists():
                mem_usage = int(memory_current.read_text().strip())
                metrics.append({
                    "metric": "container.memory.usage",
                    "value": mem_usage,
                    "timestamp": timestamp.isoformat(),
                    "tags": base_tags,
                    "unit": "bytes",
                })
            
            memory_max = cgroup_dir / "memory.max"
            if memory_max.exists():
                content = memory_max.read_text().strip()
                if content != "max":
                    metrics.append({
                        "metric": "container.memory.limit",
                        "value": int(content),
                        "timestamp": timestamp.isoformat(),
                        "tags": base_tags,
                        "unit": "bytes",
                    })
        
        return metrics
    
    async def _collect_cgroup_v1_metrics(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect metrics from cgroup v1."""
        metrics = []
        
        # Docker cgroups location
        docker_cgroups = Path("/sys/fs/cgroup/cpu/docker")
        if not docker_cgroups.exists():
            docker_cgroups = Path("/sys/fs/cgroup/cpu/system.slice")
        
        if not docker_cgroups.exists():
            return metrics
        
        for container_dir in docker_cgroups.iterdir():
            if not container_dir.is_dir():
                continue
            
            container_id = container_dir.name[:12]
            base_tags = {
                "container_id": container_id,
                **self.config.global_tags,
            }
            
            # CPU usage
            cpuacct = container_dir / "cpuacct.usage"
            if cpuacct.exists():
                usage_ns = int(cpuacct.read_text().strip())
                metrics.append({
                    "metric": "container.cpu.usage_ns",
                    "value": usage_ns,
                    "timestamp": timestamp.isoformat(),
                    "tags": base_tags,
                })
            
            # Memory usage
            mem_dir = Path(f"/sys/fs/cgroup/memory/docker/{container_dir.name}")
            if mem_dir.exists():
                memory_usage = mem_dir / "memory.usage_in_bytes"
                if memory_usage.exists():
                    metrics.append({
                        "metric": "container.memory.usage",
                        "value": int(memory_usage.read_text().strip()),
                        "timestamp": timestamp.isoformat(),
                        "tags": base_tags,
                        "unit": "bytes",
                    })
        
        return metrics
    
    def _is_container_cgroup(self, cgroup_dir: Path) -> bool:
        """Check if a cgroup directory belongs to a container."""
        path_str = str(cgroup_dir)
        container_patterns = [
            "docker",
            "containerd",
            "cri-containerd",
            "kubepods",
            "system.slice/docker",
        ]
        return any(pattern in path_str for pattern in container_patterns)
    
    def _extract_container_id(self, cgroup_dir: Path) -> Optional[str]:
        """Extract container ID from cgroup path."""
        path_str = str(cgroup_dir)
        
        # Docker: /sys/fs/cgroup/.../docker/<container_id>
        # Kubernetes: /sys/fs/cgroup/.../kubepods/.../docker-<container_id>
        
        parts = path_str.split("/")
        for i, part in enumerate(parts):
            if part == "docker" and i + 1 < len(parts):
                return parts[i + 1][:12]
            if part.startswith("docker-"):
                return part.split("-")[1][:12]
            if len(part) == 64:  # Full container ID
                return part[:12]
        
        return None
    
    def _parse_stat_file(self, path: Path) -> Dict[str, int]:
        """Parse a cgroup stat file."""
        stats = {}
        try:
            for line in path.read_text().strip().split("\n"):
                parts = line.split()
                if len(parts) == 2:
                    stats[parts[0]] = int(parts[1])
        except Exception:
            pass
        return stats
    
    def _enrich_with_k8s_metadata(
        self,
        metrics: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Add Kubernetes metadata to container metrics."""
        # Read pod info from downward API or kubelet
        pod_name = os.environ.get("POD_NAME", "")
        pod_namespace = os.environ.get("POD_NAMESPACE", "default")
        node_name = os.environ.get("NODE_NAME", "")
        
        for metric in metrics:
            if pod_name:
                metric["tags"]["pod_name"] = pod_name
            if pod_namespace:
                metric["tags"]["pod_namespace"] = pod_namespace
            if node_name:
                metric["tags"]["node_name"] = node_name
        
        return metrics
    
    async def stop(self):
        """Stop the collector."""
        pass
