"""Log collector for file-based and system logs."""

import asyncio
import fnmatch
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import hashlib

from agent.config import AgentConfig
from agent.buffer import DataBuffer

logger = logging.getLogger(__name__)


class LogCollector:
    """
    Collects logs from:
    - File-based logs (glob patterns)
    - Systemd journal
    - Docker container logs
    - Kubernetes pod logs
    
    Features:
    - Tail-based collection (new lines only)
    - Multi-line log handling
    - Log parsing and structured extraction
    - Automatic file rotation handling
    """
    
    def __init__(self, config: AgentConfig, buffer: DataBuffer):
        self.config = config
        self.buffer = buffer
        self.interval = config.log_collection_interval
        self.last_count = 0
        
        # Track file positions
        self._file_positions: Dict[str, int] = {}
        self._file_inodes: Dict[str, int] = {}
        
        # Multi-line patterns
        self._multiline_patterns = [
            re.compile(r"^\s+at\s"),  # Java stack trace
            re.compile(r"^\s+File\s"),  # Python traceback
            re.compile(r"^\s+\.\.\."),  # Continuation
        ]
        
        # Log level patterns
        self._level_patterns = {
            "error": re.compile(r"\b(ERROR|FATAL|CRITICAL|SEVERE)\b", re.I),
            "warn": re.compile(r"\b(WARN|WARNING)\b", re.I),
            "info": re.compile(r"\b(INFO)\b", re.I),
            "debug": re.compile(r"\b(DEBUG|TRACE)\b", re.I),
        }
        
        # Common log format parsers
        self._parsers = [
            self._parse_json_log,
            self._parse_common_log_format,
            self._parse_syslog_format,
        ]
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect logs from all configured sources."""
        logs = []
        
        # Collect from file paths
        for pattern in self.config.log_paths:
            file_logs = await self._collect_from_pattern(pattern)
            logs.extend(file_logs)
        
        # Collect from Docker containers
        docker_logs = await self._collect_docker_logs()
        logs.extend(docker_logs)
        
        # Collect from journald (Linux)
        journal_logs = await self._collect_journal_logs()
        logs.extend(journal_logs)
        
        # Add to buffer
        await self.buffer.add_batch("logs", logs)
        self.last_count = len(logs)
        
        return logs
    
    async def _collect_from_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """Collect logs from files matching a glob pattern."""
        logs = []
        
        # Handle recursive glob
        if "**" in pattern:
            base_path = Path(pattern.split("**")[0])
            glob_pattern = pattern.split("**")[1].lstrip("/")
            
            if base_path.exists():
                for filepath in base_path.rglob(glob_pattern):
                    if self._should_collect_file(filepath):
                        file_logs = await self._collect_from_file(filepath)
                        logs.extend(file_logs)
        else:
            base_path = Path(pattern).parent
            file_pattern = Path(pattern).name
            
            if base_path.exists():
                for filepath in base_path.glob(file_pattern):
                    if self._should_collect_file(filepath):
                        file_logs = await self._collect_from_file(filepath)
                        logs.extend(file_logs)
        
        return logs
    
    def _should_collect_file(self, filepath: Path) -> bool:
        """Check if file should be collected."""
        # Check exclude patterns
        for exclude in self.config.log_exclude_patterns:
            if fnmatch.fnmatch(filepath.name, exclude):
                return False
        
        # Check if readable
        if not filepath.is_file():
            return False
        
        try:
            # Check if file is accessible
            filepath.stat()
            return True
        except (PermissionError, OSError):
            return False
    
    async def _collect_from_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """Collect new log lines from a file."""
        logs = []
        filepath_str = str(filepath)
        
        try:
            stat = filepath.stat()
            current_inode = stat.st_ino
            current_size = stat.st_size
            
            # Check for file rotation
            stored_inode = self._file_inodes.get(filepath_str)
            if stored_inode and stored_inode != current_inode:
                # File was rotated, reset position
                self._file_positions[filepath_str] = 0
            
            self._file_inodes[filepath_str] = current_inode
            
            # Get stored position
            position = self._file_positions.get(filepath_str, 0)
            
            # Handle file truncation
            if position > current_size:
                position = 0
            
            # Read new lines
            if current_size > position:
                with open(filepath, "r", errors="ignore") as f:
                    f.seek(position)
                    
                    multiline_buffer = []
                    
                    for line in f:
                        line = line.rstrip("\n\r")
                        if not line:
                            continue
                        
                        # Handle multi-line logs
                        if self._is_continuation(line) and multiline_buffer:
                            multiline_buffer.append(line)
                        else:
                            # Process previous multi-line log
                            if multiline_buffer:
                                log_entry = self._process_log_line(
                                    "\n".join(multiline_buffer),
                                    filepath,
                                )
                                if log_entry:
                                    logs.append(log_entry)
                            
                            multiline_buffer = [line]
                    
                    # Process remaining buffer
                    if multiline_buffer:
                        log_entry = self._process_log_line(
                            "\n".join(multiline_buffer),
                            filepath,
                        )
                        if log_entry:
                            logs.append(log_entry)
                    
                    # Update position
                    self._file_positions[filepath_str] = f.tell()
        
        except Exception as e:
            logger.error(f"Error reading log file {filepath}: {e}")
        
        return logs
    
    def _is_continuation(self, line: str) -> bool:
        """Check if line is a continuation of previous log."""
        return any(pattern.match(line) for pattern in self._multiline_patterns)
    
    def _process_log_line(
        self,
        line: str,
        filepath: Path,
    ) -> Optional[Dict[str, Any]]:
        """Process a log line and extract structured data."""
        if not line.strip():
            return None
        
        # Try parsers in order
        for parser in self._parsers:
            result = parser(line)
            if result:
                result["source"] = str(filepath)
                result["source_type"] = "file"
                return result
        
        # Fallback: basic parsing
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "message": line,
            "level": self._detect_level(line),
            "source": str(filepath),
            "source_type": "file",
            "attributes": {},
        }
    
    def _detect_level(self, message: str) -> str:
        """Detect log level from message."""
        for level, pattern in self._level_patterns.items():
            if pattern.search(message):
                return level
        return "info"
    
    def _parse_json_log(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse JSON-formatted log."""
        try:
            import json
            data = json.loads(line)
            
            # Extract standard fields
            timestamp = data.get("timestamp") or data.get("time") or data.get("@timestamp")
            message = data.get("message") or data.get("msg") or data.get("log")
            level = data.get("level") or data.get("severity") or "info"
            
            if not message:
                message = line
            
            return {
                "timestamp": timestamp or datetime.utcnow().isoformat(),
                "message": message,
                "level": level.lower(),
                "attributes": {k: v for k, v in data.items() 
                             if k not in ["timestamp", "time", "@timestamp", "message", "msg", "log", "level", "severity"]},
            }
        except (json.JSONDecodeError, AttributeError):
            return None
    
    def _parse_common_log_format(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse Apache/Nginx common log format."""
        pattern = r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\d+|-)'
        match = re.match(pattern, line)
        
        if match:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": line,
                "level": "info",
                "attributes": {
                    "client_ip": match.group(1),
                    "request": match.group(3),
                    "status_code": match.group(4),
                    "bytes": match.group(5),
                },
            }
        return None
    
    def _parse_syslog_format(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse syslog format."""
        # RFC 3164 format
        pattern = r'^(<\d+>)?(\w{3}\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+):\s*(.*)'
        match = re.match(pattern, line)
        
        if match:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": match.group(5),
                "level": "info",
                "attributes": {
                    "host": match.group(3),
                    "program": match.group(4),
                },
            }
        return None
    
    async def _collect_docker_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from Docker containers."""
        logs = []
        
        # Try Docker API first (recommended approach)
        try:
            import docker
            client = docker.from_env()
            
            # Get all containers (running and stopped)
            containers = client.containers.list(all=True)
            
            for container in containers:
                try:
                    # Get logs from Docker API (last 100 lines)
                    container_logs_raw = container.logs(
                        tail=100,
                        timestamps=True,
                        since=datetime.utcnow().replace(second=0, microsecond=0).isoformat()
                    )
                    
                    # Parse logs
                    for line in container_logs_raw.decode('utf-8', errors='ignore').split('\n'):
                        if line.strip():
                            log_entry = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "message": line,
                                "level": "info",
                                "source_type": "docker",
                                "container_id": container.id[:12],
                                "container_name": container.name,
                                "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                                "attributes": {
                                    "container_id": container.id[:12],
                                    "container_name": container.name,
                                }
                            }
                            logs.append(log_entry)
                
                except Exception as e:
                    logger.debug(f"Failed to get logs from container {container.id[:12]}: {e}")
                    continue
        
        except ImportError:
            logger.debug("Docker SDK not available, trying file-based collection")
        except Exception as e:
            logger.debug(f"Docker API unavailable: {e}, trying file-based collection")
        
        # Fallback to file-based collection if Docker API fails
        if not logs:
            try:
                docker_log_path = Path("/var/lib/docker/containers")
                if docker_log_path.exists() and docker_log_path.is_dir():
                    # Check if we have permission to list directory
                    try:
                        # Test directory access - this will raise PermissionError if we can't access
                        test_list = list(docker_log_path.iterdir())
                        if not test_list:
                            # Directory is empty, nothing to collect
                            return logs
                    except (PermissionError, OSError) as e:
                        # Permission denied or other OS error - skip gracefully
                        logger.debug(f"Permission denied accessing {docker_log_path}, skipping Docker log collection: {e}")
                        return logs
                    
                    # Now iterate - we know we have permission (or at least tried to check)
                    try:
                        for container_dir in docker_log_path.iterdir():
                            if container_dir.is_dir():
                                log_file = container_dir / f"{container_dir.name}-json.log"
                                if log_file.exists() and log_file.is_file():
                                    try:
                                        container_logs = await self._collect_from_file(log_file)
                                        for log in container_logs:
                                            log["container_id"] = container_dir.name[:12]
                                            log["source_type"] = "docker"
                                        logs.extend(container_logs)
                                    except (PermissionError, OSError) as e:
                                        logger.debug(f"Permission denied reading {log_file}, skipping: {e}")
                                        continue
                                    except Exception as e:
                                        logger.debug(f"Error reading {log_file}: {e}")
                                        continue
                    except (PermissionError, OSError) as e:
                        # This shouldn't happen since we checked above, but handle it anyway
                        logger.debug(f"Permission error during iteration: {e}")
                        return logs
            except (PermissionError, OSError) as e:
                logger.debug(f"Permission denied accessing /var/lib/docker/containers, skipping Docker log collection: {e}")
            except Exception as e:
                logger.debug(f"Error accessing Docker log directory: {e}")
        
        return logs
    
    async def _collect_journal_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from systemd journal."""
        logs = []
        
        try:
            from systemd import journal
            
            j = journal.Reader()
            j.this_boot()
            j.seek_tail()
            j.get_previous()  # Move to last entry
            
            # Collect recent entries
            for entry in j:
                logs.append({
                    "timestamp": entry.get("__REALTIME_TIMESTAMP", datetime.utcnow()).isoformat(),
                    "message": entry.get("MESSAGE", ""),
                    "level": self._journal_priority_to_level(entry.get("PRIORITY", 6)),
                    "source": entry.get("SYSLOG_IDENTIFIER", "journal"),
                    "source_type": "journal",
                    "attributes": {
                        "unit": entry.get("_SYSTEMD_UNIT", ""),
                        "pid": entry.get("_PID", ""),
                    },
                })
        except ImportError:
            pass  # systemd not available
        except Exception as e:
            logger.debug(f"Journal collection failed: {e}")
        
        return logs
    
    def _journal_priority_to_level(self, priority: int) -> str:
        """Convert journal priority to log level."""
        priority_map = {
            0: "fatal",  # emerg
            1: "fatal",  # alert
            2: "fatal",  # crit
            3: "error",
            4: "warn",
            5: "info",   # notice
            6: "info",
            7: "debug",
        }
        return priority_map.get(priority, "info")
    
    async def stop(self):
        """Stop the collector."""
        pass
