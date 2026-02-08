"""Host metrics collector using psutil."""

import logging
import platform
import socket
from datetime import datetime
from typing import Any, Dict, List

import psutil

from agent.config import AgentConfig
from agent.buffer import DataBuffer

logger = logging.getLogger(__name__)


class HostMetricsCollector:
    """
    Collects host-level metrics:
    - CPU usage (overall, per-core)
    - Memory usage
    - Disk usage and I/O
    - Network I/O
    - System load
    - Process counts
    """
    
    def __init__(self, config: AgentConfig, buffer: DataBuffer):
        self.config = config
        self.buffer = buffer
        self.interval = config.host_metrics_interval
        self.last_count = 0
        
        # Cache host information
        self.host_info = self._get_host_info()
        
        # Previous values for rate calculation
        self._prev_net_io = None
        self._prev_disk_io = None
        self._prev_time = None
    
    def _get_host_info(self) -> Dict[str, str]:
        """Get static host information."""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect all host metrics."""
        now = datetime.utcnow()
        metrics = []
        
        base_tags = {
            "host": self.host_info["hostname"],
            **self.config.global_tags,
        }
        
        # CPU metrics
        metrics.extend(self._collect_cpu_metrics(now, base_tags))
        
        # Memory metrics
        metrics.extend(self._collect_memory_metrics(now, base_tags))
        
        # Disk metrics
        metrics.extend(self._collect_disk_metrics(now, base_tags))
        
        # Network metrics
        metrics.extend(self._collect_network_metrics(now, base_tags))
        
        # System metrics
        metrics.extend(self._collect_system_metrics(now, base_tags))
        
        # Add to buffer
        await self.buffer.add_batch("metrics", metrics)
        self.last_count = len(metrics)
        
        return metrics
    
    def _collect_cpu_metrics(
        self,
        timestamp: datetime,
        base_tags: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Collect CPU metrics."""
        metrics = []
        
        # Overall CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        metrics.append({
            "metric": "system.cpu.usage",  # API expects "metric" not "name"
            "value": cpu_percent,
            "timestamp": timestamp.isoformat(),
            "tags": {**base_tags, "type": "total"},
            "unit": "percent",
        })
        
        # Per-CPU
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        for i, cpu in enumerate(per_cpu):
            metrics.append({
                "metric": "system.cpu.usage",
                "value": cpu,
                "timestamp": timestamp.isoformat(),
                "tags": {**base_tags, "cpu": str(i)},
                "unit": "percent",
            })
        
        # CPU times
        cpu_times = psutil.cpu_times_percent(interval=None)
        for field in ["user", "system", "idle", "iowait"]:
            value = getattr(cpu_times, field, None)
            if value is not None:
                metrics.append({
                    "metric": f"system.cpu.{field}",
                    "value": value,
                    "timestamp": timestamp.isoformat(),
                    "tags": base_tags,
                    "unit": "percent",
                })
        
        # Load average (Unix only)
        try:
            load = psutil.getloadavg()
            for i, period in enumerate(["1m", "5m", "15m"]):
                metrics.append({
                    "metric": "system.load.average",
                    "value": load[i],
                    "timestamp": timestamp.isoformat(),
                    "tags": {**base_tags, "period": period},
                })
        except (AttributeError, OSError):
            pass  # Windows doesn't have load average
        
        return metrics
    
    def _collect_memory_metrics(
        self,
        timestamp: datetime,
        base_tags: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Collect memory metrics."""
        metrics = []
        
        # Virtual memory
        mem = psutil.virtual_memory()
        metrics.extend([
            {
                "metric": "system.memory.total",
                "value": mem.total,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "bytes",
            },
            {
                "metric": "system.memory.used",
                "value": mem.used,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "bytes",
            },
            {
                "metric": "system.memory.available",
                "value": mem.available,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "bytes",
            },
            {
                "metric": "system.memory.usage",
                "value": mem.percent,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "percent",
            },
        ])
        
        # Swap
        swap = psutil.swap_memory()
        metrics.extend([
            {
                "metric": "system.swap.total",
                "value": swap.total,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "bytes",
            },
            {
                "metric": "system.swap.used",
                "value": swap.used,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "bytes",
            },
            {
                "metric": "system.swap.usage",
                "value": swap.percent,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
                "unit": "percent",
            },
        ])
        
        return metrics
    
    def _collect_disk_metrics(
        self,
        timestamp: datetime,
        base_tags: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Collect disk metrics."""
        metrics = []
        
        # Disk partitions
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                tags = {
                    **base_tags,
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                }
                
                metrics.extend([
                    {
                        "metric": "system.disk.total",
                        "value": usage.total,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                        "unit": "bytes",
                    },
                    {
                        "metric": "system.disk.used",
                        "value": usage.used,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                        "unit": "bytes",
                    },
                    {
                        "metric": "system.disk.free",
                        "value": usage.free,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                        "unit": "bytes",
                    },
                    {
                        "metric": "system.disk.usage",
                        "value": usage.percent,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                        "unit": "percent",
                    },
                ])
            except (PermissionError, OSError):
                continue
        
        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters(perdisk=True)
            now = datetime.utcnow()
            
            for disk, counters in disk_io.items():
                tags = {**base_tags, "disk": disk}
                
                metrics.extend([
                    {
                        "metric": "system.disk.read_bytes",
                        "value": counters.read_bytes,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                        "unit": "bytes",
                    },
                    {
                        "metric": "system.disk.write_bytes",
                        "value": counters.write_bytes,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                        "unit": "bytes",
                    },
                    {
                        "metric": "system.disk.read_count",
                        "value": counters.read_count,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                    },
                    {
                        "metric": "system.disk.write_count",
                        "value": counters.write_count,
                        "timestamp": timestamp.isoformat(),
                        "tags": tags,
                    },
                ])
        except Exception:
            pass
        
        return metrics
    
    def _collect_network_metrics(
        self,
        timestamp: datetime,
        base_tags: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Collect network metrics."""
        metrics = []
        
        # Network I/O per interface
        net_io = psutil.net_io_counters(pernic=True)
        
        for interface, counters in net_io.items():
            tags = {**base_tags, "interface": interface}
            
            metrics.extend([
                {
                    "metric": "system.network.bytes_sent",
                    "value": counters.bytes_sent,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                    "unit": "bytes",
                },
                {
                    "metric": "system.network.bytes_recv",
                    "value": counters.bytes_recv,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                    "unit": "bytes",
                },
                {
                    "metric": "system.network.packets_sent",
                    "value": counters.packets_sent,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "system.network.packets_recv",
                    "value": counters.packets_recv,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "system.network.errors_in",
                    "value": counters.errin,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "system.network.errors_out",
                    "value": counters.errout,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "system.network.drops_in",
                    "value": counters.dropin,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
                {
                    "metric": "system.network.drops_out",
                    "value": counters.dropout,
                    "timestamp": timestamp.isoformat(),
                    "tags": tags,
                },
            ])
        
        return metrics
    
    def _collect_system_metrics(
        self,
        timestamp: datetime,
        base_tags: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Collect system-level metrics."""
        metrics = []
        
        # Boot time
        boot_time = psutil.boot_time()
        uptime = datetime.utcnow().timestamp() - boot_time
        metrics.append({
            "metric": "system.uptime",
            "value": uptime,
            "timestamp": timestamp.isoformat(),
            "tags": base_tags,
            "unit": "seconds",
        })
        
        # Process counts
        pids = psutil.pids()
        metrics.append({
            "metric": "system.processes.count",
            "value": len(pids),
            "timestamp": timestamp.isoformat(),
            "tags": base_tags,
        })
        
        # File descriptors (Unix)
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            metrics.append({
                "metric": "system.fd.limit",
                "value": soft,
                "timestamp": timestamp.isoformat(),
                "tags": base_tags,
            })
        except (ImportError, AttributeError):
            pass
        
        return metrics
    
    async def stop(self):
        """Stop the collector."""
        pass
