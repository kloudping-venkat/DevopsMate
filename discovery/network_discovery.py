"""Network connection discovery for topology building."""

import logging
import socket
import ipaddress
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil

from agent.config import AgentConfig

logger = logging.getLogger(__name__)


class NetworkDiscovery:
    """
    Discovers network connections to build service topology:
    - Process-to-process connections
    - Service-to-database connections
    - External dependencies
    - Load balancer relationships
    
    This is the foundation for Smartscape-like topology visualization.
    """
    
    # Well-known ports for service identification
    WELL_KNOWN_PORTS = {
        # Databases
        5432: "postgresql",
        3306: "mysql",
        27017: "mongodb",
        6379: "redis",
        9042: "cassandra",
        9200: "elasticsearch",
        
        # Message queues
        5672: "rabbitmq",
        9092: "kafka",
        4222: "nats",
        
        # HTTP
        80: "http",
        443: "https",
        8080: "http-alt",
        8443: "https-alt",
        
        # Other
        22: "ssh",
        53: "dns",
        25: "smtp",
        389: "ldap",
        636: "ldaps",
    }
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        # Cache for hostname resolution
        self._hostname_cache: Dict[str, str] = {}
        
        # Discovered connections
        self._connections: List[Dict[str, Any]] = []
    
    async def discover(self) -> List[Dict[str, Any]]:
        """Discover all network connections."""
        connections = []
        seen_connections: Set[Tuple] = set()
        
        try:
            net_connections = psutil.net_connections(kind="inet")
        except psutil.AccessDenied:
            logger.warning("Access denied for network connections")
            return connections
        
        # Process mapping
        pid_to_process = {}
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pid_to_process[proc.info['pid']] = {
                    "name": proc.info['name'],
                    "cmdline": ' '.join(proc.info['cmdline'] or [])[:200],
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        for conn in net_connections:
            if not conn.laddr or not conn.raddr:
                continue
            
            # Skip loopback and special addresses
            raddr_ip = conn.raddr.ip
            if not raddr_ip or raddr_ip in ("0.0.0.0", "::", "::1", "127.0.0.1", "localhost"):
                continue
            
            # Skip IPv6 if not supported or if it's a loopback
            if raddr_ip.startswith("127.") or raddr_ip.startswith("::"):
                continue
            
            # Create unique connection key
            conn_key = (
                conn.pid,
                conn.laddr.port,
                conn.raddr.ip,
                conn.raddr.port,
            )
            
            if conn_key in seen_connections:
                continue
            seen_connections.add(conn_key)
            
            # Get process info
            process_info = pid_to_process.get(conn.pid, {"name": "unknown", "cmdline": ""})
            
            # Identify remote service type
            remote_service = self._identify_service(conn.raddr.port, conn.raddr.ip)
            
            # Resolve hostname (with error handling)
            try:
                remote_hostname = self._resolve_hostname(conn.raddr.ip)
            except Exception as e:
                logger.debug(f"Could not resolve hostname for {conn.raddr.ip}: {e}")
                remote_hostname = conn.raddr.ip
            
            connection_info = {
                "local_pid": conn.pid,
                "local_process": process_info["name"],
                "local_cmdline": process_info["cmdline"],
                "local_addr": conn.laddr.ip,
                "local_port": conn.laddr.port,
                "remote_addr": conn.raddr.ip,
                "remote_hostname": remote_hostname,
                "remote_port": conn.raddr.port,
                "remote_service": remote_service,
                "status": conn.status,
                "protocol": "tcp" if conn.type == socket.SOCK_STREAM else "udp",
                "direction": self._determine_direction(conn),
                "discovered_at": datetime.utcnow().isoformat(),
            }
            
            connections.append(connection_info)
        
        self._connections = connections
        logger.info(f"Discovered {len(connections)} network connections")
        
        return connections
    
    def _identify_service(self, port: int, ip: str) -> str:
        """Identify the service based on port."""
        if port in self.WELL_KNOWN_PORTS:
            return self.WELL_KNOWN_PORTS[port]
        
        if port >= 30000 and port <= 32767:
            return "kubernetes-nodeport"
        
        if port >= 49152:
            return "ephemeral"
        
        return "unknown"
    
    def _resolve_hostname(self, ip: str) -> str:
        """Resolve IP to hostname with caching."""
        if ip in self._hostname_cache:
            return self._hostname_cache[ip]
        
        # Skip special addresses that can't be resolved
        if not ip or ip in ("0.0.0.0", "::", "::1", "127.0.0.1", "localhost"):
            self._hostname_cache[ip] = ip
            return ip
        
        # Validate IP address format and handle IPv6
        try:
            parsed_ip = ipaddress.ip_address(ip)
            
            # Skip IPv6 addresses that might cause issues
            if isinstance(parsed_ip, ipaddress.IPv6Address):
                # For IPv6, check if it's a link-local, loopback, or multicast address
                if parsed_ip.is_link_local or parsed_ip.is_loopback or parsed_ip.is_multicast:
                    self._hostname_cache[ip] = ip
                    return ip
                # Skip IPv6 resolution if IPv6 is not properly configured (will be caught by OSError)
        except ValueError:
            # Not a valid IP address, return as-is
            self._hostname_cache[ip] = ip
            return ip
        
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            self._hostname_cache[ip] = hostname
            return hostname
        except (socket.herror, socket.gaierror, OSError, ValueError) as e:
            # Handle all possible errors:
            # - socket.herror: Host not found
            # - socket.gaierror: Address-related error
            # - OSError: Address family not supported (Errno 97) or other OS errors
            # - ValueError: Invalid IP address format
            logger.debug(f"Could not resolve hostname for {ip}: {e}")
            self._hostname_cache[ip] = ip
            return ip
    
    def _determine_direction(self, conn) -> str:
        """Determine if connection is inbound or outbound."""
        # If local port is well-known or lower, likely inbound
        if conn.laddr.port in self.WELL_KNOWN_PORTS:
            return "inbound"
        
        # If remote port is well-known, likely outbound
        if conn.raddr.port in self.WELL_KNOWN_PORTS:
            return "outbound"
        
        # If local port is lower, likely inbound (server)
        if conn.laddr.port < conn.raddr.port:
            return "inbound"
        
        return "outbound"
    
    def get_service_dependencies(self) -> Dict[str, List[str]]:
        """Build a map of service dependencies from connections."""
        dependencies: Dict[str, Set[str]] = {}
        
        for conn in self._connections:
            local = conn["local_process"]
            remote = conn["remote_service"]
            
            if remote and remote != "unknown" and remote != "ephemeral":
                if local not in dependencies:
                    dependencies[local] = set()
                dependencies[local].add(f"{remote}:{conn['remote_addr']}")
        
        return {k: list(v) for k, v in dependencies.items()}
    
    def get_topology_edges(self) -> List[Dict[str, Any]]:
        """Get edges for topology graph."""
        edges = []
        seen_edges: Set[Tuple] = set()
        
        for conn in self._connections:
            if conn["direction"] == "outbound":
                edge_key = (conn["local_process"], conn["remote_service"], conn["remote_port"])
                
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source": conn["local_process"],
                        "target": f"{conn['remote_service']}:{conn['remote_addr']}",
                        "port": conn["remote_port"],
                        "protocol": conn["protocol"],
                    })
        
        return edges
