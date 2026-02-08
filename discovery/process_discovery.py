"""Process discovery for auto-detecting services and technologies."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil

from agent.config import AgentConfig

logger = logging.getLogger(__name__)


class ProcessDiscovery:
    """
    Discovers running processes and identifies:
    - Service type (web server, database, queue, etc.)
    - Technology stack (Java, Node.js, Python, Go, .NET)
    - Framework (Spring, Express, Django, etc.)
    - Listening ports
    - Process relationships
    
    This enables Dynatrace-like auto-discovery without manual configuration.
    """
    
    # Technology detection patterns
    TECHNOLOGY_PATTERNS = {
        "java": {
            "cmdline_patterns": [r"java\s", r"\.jar\b"],
            "process_names": ["java", "java.exe"],
            "frameworks": {
                "spring": [r"spring", r"org\.springframework"],
                "tomcat": [r"catalina", r"tomcat"],
                "wildfly": [r"wildfly", r"jboss"],
                "jetty": [r"jetty"],
            },
        },
        "nodejs": {
            "cmdline_patterns": [r"node\s", r"nodejs\s", r"npm\s"],
            "process_names": ["node", "node.exe", "nodejs"],
            "frameworks": {
                "express": [r"express"],
                "nestjs": [r"@nestjs"],
                "fastify": [r"fastify"],
                "nextjs": [r"next"],
            },
        },
        "python": {
            "cmdline_patterns": [r"python\s", r"python3\s", r"\.py\b"],
            "process_names": ["python", "python3", "python.exe"],
            "frameworks": {
                "django": [r"django", r"manage\.py"],
                "flask": [r"flask"],
                "fastapi": [r"fastapi", r"uvicorn"],
                "celery": [r"celery"],
            },
        },
        "go": {
            "cmdline_patterns": [],  # Go binaries are compiled
            "process_names": [],
            "detection_method": "elf_check",
        },
        "dotnet": {
            "cmdline_patterns": [r"dotnet\s", r"\.dll\b"],
            "process_names": ["dotnet", "dotnet.exe"],
            "frameworks": {
                "aspnet": [r"Microsoft\.AspNetCore"],
            },
        },
        "ruby": {
            "cmdline_patterns": [r"ruby\s", r"\.rb\b", r"rails\s"],
            "process_names": ["ruby", "ruby.exe"],
            "frameworks": {
                "rails": [r"rails"],
                "sinatra": [r"sinatra"],
            },
        },
        "php": {
            "cmdline_patterns": [r"php\s", r"php-fpm"],
            "process_names": ["php", "php-fpm", "php.exe"],
            "frameworks": {
                "laravel": [r"laravel", r"artisan"],
                "symfony": [r"symfony"],
            },
        },
    }
    
    # Service type detection
    SERVICE_PATTERNS = {
        "web_server": {
            "process_names": ["nginx", "apache2", "httpd", "caddy", "haproxy"],
            "ports": [80, 443, 8080, 8443],
        },
        "database": {
            "process_names": ["postgres", "mysqld", "mongod", "redis-server", "cassandra"],
            "ports": [5432, 3306, 27017, 6379, 9042],
        },
        "message_queue": {
            "process_names": ["rabbitmq", "kafka", "nats-server"],
            "ports": [5672, 9092, 4222],
        },
        "cache": {
            "process_names": ["redis-server", "memcached"],
            "ports": [6379, 11211],
        },
        "search": {
            "process_names": ["elasticsearch", "solr"],
            "ports": [9200, 8983],
        },
    }
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._exclude_patterns = [
            re.compile(p) for p in config.process_exclude_patterns
        ]
    
    async def discover(self) -> List[Dict[str, Any]]:
        """Discover all processes and their metadata."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username', 'create_time']):
            try:
                proc_info = self._analyze_process(proc)
                if proc_info and not self._should_exclude(proc_info):
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        logger.info(f"Discovered {len(processes)} processes")
        return processes
    
    def _analyze_process(self, proc: psutil.Process) -> Optional[Dict[str, Any]]:
        """Analyze a single process."""
        try:
            info = proc.info
            pid = info['pid']
            name = info['name'] or ''
            cmdline = info['cmdline'] or []
            cmdline_str = ' '.join(cmdline)
            
            # Detect technology
            technology = self._detect_technology(name, cmdline_str)
            
            # Detect framework
            framework = self._detect_framework(technology, cmdline_str)
            
            # Detect service type
            service_type = self._detect_service_type(name, proc)
            
            # Get listening ports
            listening_ports = self._get_listening_ports(proc)
            
            # Get connections (for topology)
            connections = self._get_connections(proc)
            
            # Get memory and CPU
            try:
                memory_info = proc.memory_info()
                cpu_percent = proc.cpu_percent(interval=0.1)
            except Exception:
                memory_info = None
                cpu_percent = 0
            
            return {
                "pid": pid,
                "name": name,
                "cmdline": cmdline_str[:500],  # Truncate
                "username": info.get('username', ''),
                "technology": technology,
                "framework": framework,
                "service_type": service_type,
                "listening_ports": listening_ports,
                "connections": connections,
                "memory_rss": memory_info.rss if memory_info else 0,
                "cpu_percent": cpu_percent,
                "create_time": datetime.fromtimestamp(info['create_time']).isoformat() if info['create_time'] else None,
                "discovered_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.debug(f"Error analyzing process: {e}")
            return None
    
    def _detect_technology(self, name: str, cmdline: str) -> Optional[str]:
        """Detect the technology/runtime of a process."""
        name_lower = name.lower()
        cmdline_lower = cmdline.lower()
        
        for tech, patterns in self.TECHNOLOGY_PATTERNS.items():
            # Check process name
            if any(pn in name_lower for pn in patterns.get("process_names", [])):
                return tech
            
            # Check command line
            for pattern in patterns.get("cmdline_patterns", []):
                if re.search(pattern, cmdline_lower):
                    return tech
        
        return None
    
    def _detect_framework(self, technology: Optional[str], cmdline: str) -> Optional[str]:
        """Detect the framework being used."""
        if not technology:
            return None
        
        cmdline_lower = cmdline.lower()
        tech_patterns = self.TECHNOLOGY_PATTERNS.get(technology, {})
        frameworks = tech_patterns.get("frameworks", {})
        
        for framework, patterns in frameworks.items():
            for pattern in patterns:
                if re.search(pattern, cmdline_lower):
                    return framework
        
        return None
    
    def _detect_service_type(self, name: str, proc: psutil.Process) -> Optional[str]:
        """Detect the type of service."""
        name_lower = name.lower()
        
        for service_type, config in self.SERVICE_PATTERNS.items():
            # Check process name
            if any(pn in name_lower for pn in config["process_names"]):
                return service_type
            
            # Check listening ports
            try:
                for conn in proc.connections(kind="inet"):
                    if conn.status == "LISTEN" and conn.laddr.port in config["ports"]:
                        return service_type
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        
        return "application"  # Default
    
    def _get_listening_ports(self, proc: psutil.Process) -> List[int]:
        """Get ports the process is listening on."""
        ports = []
        try:
            for conn in proc.connections(kind="inet"):
                if conn.status == "LISTEN":
                    ports.append(conn.laddr.port)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return sorted(set(ports))
    
    def _get_connections(self, proc: psutil.Process) -> List[Dict[str, Any]]:
        """Get outgoing connections for topology mapping."""
        connections = []
        try:
            for conn in proc.connections(kind="inet"):
                if conn.status == "ESTABLISHED" and conn.raddr:
                    connections.append({
                        "local_port": conn.laddr.port,
                        "remote_addr": conn.raddr.ip,
                        "remote_port": conn.raddr.port,
                    })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return connections[:50]  # Limit
    
    def _should_exclude(self, proc_info: Dict[str, Any]) -> bool:
        """Check if process should be excluded."""
        name = proc_info.get("name", "")
        
        for pattern in self._exclude_patterns:
            if pattern.match(name):
                return True
        
        return False
