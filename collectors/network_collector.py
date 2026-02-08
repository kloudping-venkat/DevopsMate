"""Network metrics and flow collector."""

import asyncio
import logging
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

import psutil

from agent.config import AgentConfig
from agent.buffer import DataBuffer

logger = logging.getLogger(__name__)


class NetworkCollector:
    """
    Collects network metrics and connection information:
    - Network interface statistics
    - Active connections
    - Connection states
    - Process-to-connection mapping (for topology)
    
    This enables service dependency discovery by tracking
    which processes connect to which endpoints.
    """
    
    def __init__(self, config: AgentConfig, buffer: DataBuffer):
        self.config = config
        self.buffer = buffer
        self.interval = config.network_metrics_interval
        self.last_count = 0
        
        # Cache for connection tracking
        self._prev_connections: Dict[str, Dict] = {}
        self._connection_history: List[Dict] = []
        
        # Sampling
        self.sample_rate = config.network_sample_rate
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect network metrics and connections."""
        metrics = []
        now = datetime.utcnow()
        
        # Interface metrics
        interface_metrics = self._collect_interface_metrics(now)
        metrics.extend(interface_metrics)
        
        # Connection metrics
        connection_metrics = await self._collect_connection_metrics(now)
        metrics.extend(connection_metrics)
        
        # Protocol statistics
        protocol_metrics = self._collect_protocol_stats(now)
        metrics.extend(protocol_metrics)
        
        # Add to buffer
        await self.buffer.add_batch("metrics", metrics)
        self.last_count = len(metrics)
        
        return metrics
    
    def _collect_interface_metrics(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect per-interface network metrics."""
        metrics = []
        
        net_io = psutil.net_io_counters(pernic=True)
        
        for interface, counters in net_io.items():
            tags = {
                "interface": interface,
                **self.config.global_tags,
            }
            
            # Calculate rates if we have previous values
            metrics.extend([
                {
                    "metric": "network.interface.bytes_sent_total",
                    "value": counters.bytes_sent,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                    "unit": "bytes",
                },
                {
                    "metric": "network.interface.bytes_recv_total",
                    "value": counters.bytes_recv,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                    "unit": "bytes",
                },
                {
                    "metric": "network.interface.packets_sent_total",
                    "value": counters.packets_sent,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "network.interface.packets_recv_total",
                    "value": counters.packets_recv,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "network.interface.errors_in",
                    "value": counters.errin,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "network.interface.errors_out",
                    "value": counters.errout,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "network.interface.drops_in",
                    "value": counters.dropin,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "network.interface.drops_out",
                    "value": counters.dropout,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
            ])
        
        return metrics
    
    async def _collect_connection_metrics(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect active connection metrics."""
        metrics = []
        
        try:
            connections = psutil.net_connections(kind="all")
        except psutil.AccessDenied:
            logger.warning("Access denied for network connections, running as non-root")
            return metrics
        
        # Count connections by state
        state_counts = defaultdict(int)
        protocol_counts = defaultdict(int)
        
        # Track connections for topology
        connection_flows = []
        
        for conn in connections:
            # Count by state
            state = conn.status if hasattr(conn, "status") else "UNKNOWN"
            state_counts[state] += 1
            
            # Count by protocol
            if conn.type == socket.SOCK_STREAM:
                protocol_counts["tcp"] += 1
            elif conn.type == socket.SOCK_DGRAM:
                protocol_counts["udp"] += 1
            
            # Extract connection flow for topology
            if conn.laddr and conn.raddr:
                flow = {
                    "local_addr": conn.laddr.ip if conn.laddr else None,
                    "local_port": conn.laddr.port if conn.laddr else None,
                    "remote_addr": conn.raddr.ip if conn.raddr else None,
                    "remote_port": conn.raddr.port if conn.raddr else None,
                    "pid": conn.pid,
                    "status": state,
                    "protocol": "tcp" if conn.type == socket.SOCK_STREAM else "udp",
                }
                
                # Apply sampling
                import random
                if random.random() < self.sample_rate:
                    connection_flows.append(flow)
        
        # Connection state metrics
        for state, count in state_counts.items():
            metrics.append({
                "metric": "network.connections.by_state",
                "value": count,
                "timestamp": timestamp.isoformat(),
                "tags": {
                    "state": state,
                    **self.config.global_tags,
                },
            })
        
        # Protocol metrics
        for protocol, count in protocol_counts.items():
            metrics.append({
                "metric": "network.connections.by_protocol",
                "value": count,
                "timestamp": timestamp.isoformat(),
                "tags": {
                    "protocol": protocol,
                    **self.config.global_tags,
                },
            })
        
        # Total connections
        metrics.append({
            "metric": "network.connections.total",
            "value": len(connections),
            "timestamp": timestamp.isoformat(),
            "tags": self.config.global_tags,
        })
        
        # Store connection flows for topology
        self._connection_history = connection_flows
        
        return metrics
    
    def _collect_protocol_stats(
        self,
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """Collect protocol-level statistics."""
        metrics = []
        
        try:
            # TCP stats
            tcp_stats = psutil.net_if_stats()
            
            # Socket statistics from /proc/net/snmp (Linux)
            snmp_stats = self._read_snmp_stats()
            
            if snmp_stats:
                # TCP metrics
                if "Tcp" in snmp_stats:
                    tcp = snmp_stats["Tcp"]
                    tcp_metrics = {
                        "network.tcp.active_opens": tcp.get("ActiveOpens", 0),
                        "network.tcp.passive_opens": tcp.get("PassiveOpens", 0),
                        "network.tcp.attempt_fails": tcp.get("AttemptFails", 0),
                        "network.tcp.estab_resets": tcp.get("EstabResets", 0),
                        "network.tcp.curr_estab": tcp.get("CurrEstab", 0),
                        "network.tcp.retrans_segs": tcp.get("RetransSegs", 0),
                        "network.tcp.in_errs": tcp.get("InErrs", 0),
                        "network.tcp.out_rsts": tcp.get("OutRsts", 0),
                    }
                    
                    for name, value in tcp_metrics.items():
                        metrics.append({
                            "metric": name,
                            "value": value,
                            "timestamp": timestamp.isoformat(),
                            "tags": self.config.global_tags,
                        })
                
                # UDP metrics
                if "Udp" in snmp_stats:
                    udp = snmp_stats["Udp"]
                    udp_metrics = {
                        "network.udp.in_datagrams": udp.get("InDatagrams", 0),
                        "network.udp.no_ports": udp.get("NoPorts", 0),
                        "network.udp.in_errors": udp.get("InErrors", 0),
                        "network.udp.out_datagrams": udp.get("OutDatagrams", 0),
                    }
                    
                    for name, value in udp_metrics.items():
                        metrics.append({
                            "metric": name,
                            "value": value,
                            "timestamp": timestamp.isoformat(),
                            "tags": self.config.global_tags,
                        })
        
        except Exception as e:
            logger.debug(f"Protocol stats collection failed: {e}")
        
        return metrics
    
    def _read_snmp_stats(self) -> Dict[str, Dict[str, int]]:
        """Read /proc/net/snmp for protocol statistics."""
        stats = {}
        
        try:
            with open("/proc/net/snmp", "r") as f:
                lines = f.readlines()
            
            i = 0
            while i < len(lines) - 1:
                header_line = lines[i].strip()
                value_line = lines[i + 1].strip()
                
                if ": " in header_line:
                    protocol, headers = header_line.split(": ", 1)
                    _, values = value_line.split(": ", 1)
                    
                    header_list = headers.split()
                    value_list = [int(v) for v in values.split()]
                    
                    stats[protocol] = dict(zip(header_list, value_list))
                
                i += 2
        
        except FileNotFoundError:
            pass  # Not Linux
        except Exception as e:
            logger.debug(f"Failed to read SNMP stats: {e}")
        
        return stats
    
    def get_connection_flows(self) -> List[Dict[str, Any]]:
        """Get recent connection flows for topology building."""
        return self._connection_history.copy()
    
    async def stop(self):
        """Stop the collector."""
        pass
