"""Container and Kubernetes discovery."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.config import AgentConfig

logger = logging.getLogger(__name__)


class ContainerDiscovery:
    """
    Discovers containers and their metadata:
    - Docker containers
    - Kubernetes pods
    - Container images
    - Labels and annotations
    - Resource limits
    
    Enables automatic service catalog population.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._docker_client = None
        self._k8s_client = None
    
    async def discover(self) -> List[Dict[str, Any]]:
        """Discover all containers."""
        containers = []
        
        # Discover Docker containers
        docker_containers = await self._discover_docker()
        containers.extend(docker_containers)
        
        # Discover Kubernetes pods
        if self.config.kubernetes_enabled:
            k8s_pods = await self._discover_kubernetes()
            containers.extend(k8s_pods)
        
        return containers
    
    async def _discover_docker(self) -> List[Dict[str, Any]]:
        """Discover Docker containers."""
        containers = []
        
        try:
            import docker
            client = docker.from_env()
            
            for container in client.containers.list(all=True):
                containers.append({
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "status": container.status,
                    "state": container.attrs.get("State", {}).get("Status", "unknown"),
                    "created": container.attrs.get("Created", ""),
                    "labels": container.labels,
                    "ports": self._extract_ports(container),
                    "networks": list(container.attrs.get("NetworkSettings", {}).get("Networks", {}).keys()),
                    "env_vars": self._extract_env_hints(container),
                    "resource_limits": self._extract_resource_limits(container),
                    "runtime": "docker",
                    "discovered_at": datetime.utcnow().isoformat(),
                })
        
        except ImportError:
            logger.debug("Docker SDK not available")
        except Exception as e:
            logger.error(f"Docker discovery failed: {e}")
        
        return containers
    
    def _extract_ports(self, container) -> List[Dict[str, Any]]:
        """Extract port mappings from container."""
        ports = []
        
        port_bindings = container.attrs.get("HostConfig", {}).get("PortBindings", {}) or {}
        
        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                for binding in host_bindings:
                    ports.append({
                        "container_port": container_port,
                        "host_ip": binding.get("HostIp", "0.0.0.0"),
                        "host_port": binding.get("HostPort", ""),
                    })
        
        return ports
    
    def _extract_env_hints(self, container) -> Dict[str, str]:
        """Extract useful environment variable hints (non-sensitive)."""
        hints = {}
        
        env_list = container.attrs.get("Config", {}).get("Env", []) or []
        
        # Only extract non-sensitive vars that help identify the service
        safe_prefixes = [
            "SERVICE_", "APP_", "SERVER_", "NODE_ENV", "FLASK_", "DJANGO_",
            "SPRING_", "RAILS_ENV", "PORT", "HOST",
        ]
        
        for env in env_list:
            if "=" in env:
                key, value = env.split("=", 1)
                if any(key.startswith(prefix) for prefix in safe_prefixes):
                    # Don't include values that look like secrets
                    if not any(s in key.lower() for s in ["password", "secret", "key", "token"]):
                        hints[key] = value[:100]  # Truncate
        
        return hints
    
    def _extract_resource_limits(self, container) -> Dict[str, Any]:
        """Extract resource limits from container."""
        host_config = container.attrs.get("HostConfig", {})
        
        return {
            "memory_limit": host_config.get("Memory", 0),
            "memory_reservation": host_config.get("MemoryReservation", 0),
            "cpu_shares": host_config.get("CpuShares", 0),
            "cpu_quota": host_config.get("CpuQuota", 0),
            "cpu_period": host_config.get("CpuPeriod", 0),
        }
    
    async def _discover_kubernetes(self) -> List[Dict[str, Any]]:
        """Discover Kubernetes pods."""
        pods = []
        
        try:
            from kubernetes import client, config
            
            # Load config
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
            
            v1 = client.CoreV1Api()
            
            # Get pods in current namespace or all namespaces
            namespace = os.environ.get("POD_NAMESPACE")
            
            if namespace:
                pod_list = v1.list_namespaced_pod(namespace)
            else:
                pod_list = v1.list_pod_for_all_namespaces()
            
            for pod in pod_list.items:
                pod_info = {
                    "id": pod.metadata.uid,
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "node_name": pod.spec.node_name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "labels": pod.metadata.labels or {},
                    "annotations": pod.metadata.annotations or {},
                    "containers": [],
                    "runtime": "kubernetes",
                    "discovered_at": datetime.utcnow().isoformat(),
                }
                
                # Extract container info
                for container in pod.spec.containers:
                    container_info = {
                        "name": container.name,
                        "image": container.image,
                        "ports": [],
                        "resource_limits": {},
                        "resource_requests": {},
                    }
                    
                    # Ports
                    if container.ports:
                        container_info["ports"] = [
                            {"port": p.container_port, "protocol": p.protocol, "name": p.name}
                            for p in container.ports
                        ]
                    
                    # Resources
                    if container.resources:
                        if container.resources.limits:
                            container_info["resource_limits"] = dict(container.resources.limits)
                        if container.resources.requests:
                            container_info["resource_requests"] = dict(container.resources.requests)
                    
                    pod_info["containers"].append(container_info)
                
                # Add owner references (deployment, statefulset, etc.)
                if pod.metadata.owner_references:
                    owner = pod.metadata.owner_references[0]
                    pod_info["owner"] = {
                        "kind": owner.kind,
                        "name": owner.name,
                    }
                
                pods.append(pod_info)
        
        except ImportError:
            logger.debug("Kubernetes client not available")
        except Exception as e:
            logger.error(f"Kubernetes discovery failed: {e}")
        
        return pods
    
    async def get_container_by_id(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get specific container by ID."""
        containers = await self.discover()
        
        for container in containers:
            if container["id"].startswith(container_id):
                return container
        
        return None
