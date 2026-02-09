"""Data buffer for the agent with persistence support."""

import asyncio
import json
import logging
import shutil
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import gzip

logger = logging.getLogger(__name__)


@dataclass
class BufferedData:
    """A piece of buffered data."""
    data_type: str  # "metrics", "logs", "traces", "topology"
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    attempts: int = 0


class DataBuffer:
    """
    In-memory buffer with disk spillover for reliability.
    
    Features:
    - In-memory queue for speed
    - Disk spillover when memory limit reached
    - Automatic retry with backoff
    - Data persistence across agent restarts
    """
    
    def __init__(
        self,
        max_size: int = 10000,
        flush_interval: float = 10.0,
        spill_path: Optional[str] = None,
        max_spill_size_mb: int = 100,
        max_disk_ratio: float = 0.95,  # Don't use more than 95% of disk
        flush_to_disk_mem_ratio: float = 0.5,  # Flush 50% of buffer when full
    ):
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.max_disk_ratio = max_disk_ratio
        self.flush_to_disk_mem_ratio = flush_to_disk_mem_ratio
        
        # Use installation directory for spill path (user-writable)
        # Fallback to /var/lib/devopsmate/buffer if explicitly provided
        if spill_path:
            self.spill_path = Path(spill_path)
        else:
            # Use user's home directory or current working directory
            import os
            base_path = os.getenv("DEVOPSMATE_AGENT_DIR", os.getcwd())
            self.spill_path = Path(base_path) / "buffer"
        self.max_spill_size = max_spill_size_mb * 1024 * 1024
        
        # In-memory buffers by type
        self._buffers: Dict[str, deque] = {
            "metrics": deque(maxlen=max_size),
            "logs": deque(maxlen=max_size),
            "traces": deque(maxlen=max_size),
            "topology": deque(maxlen=1000),
        }
        
        self._lock = asyncio.Lock()
        self._stats = {
            "total_added": 0,
            "total_flushed": 0,
            "spill_count": 0,
            "drop_count": 0,
        }
    
    async def add(self, data_type: str, data: Dict[str, Any]) -> bool:
        """Add data to the buffer."""
        async with self._lock:
            if data_type not in self._buffers:
                logger.warning(f"Unknown data type: {data_type}")
                return False
            
            buffered = BufferedData(
                data_type=data_type,
                payload=data,
            )
            
            buffer = self._buffers[data_type]
            
            # Check if buffer is full
            if len(buffer) >= self.max_size:
                # Try to spill to disk
                if not await self._spill_to_disk(data_type):
                    self._stats["drop_count"] += 1
                    return False
            
            buffer.append(buffered)
            self._stats["total_added"] += 1
            return True
    
    async def add_batch(self, data_type: str, items: List[Dict[str, Any]]) -> int:
        """Add multiple items to the buffer."""
        added = 0
        for item in items:
            if await self.add(data_type, item):
                added += 1
        return added
    
    async def get_batch(self, data_type: str, max_items: int = 1000) -> List[BufferedData]:
        """Get a batch of items from the buffer."""
        async with self._lock:
            if data_type not in self._buffers:
                return []
            
            buffer = self._buffers[data_type]
            batch = []
            
            while buffer and len(batch) < max_items:
                batch.append(buffer.popleft())
            
            self._stats["total_flushed"] += len(batch)
            return batch
    
    async def return_failed(self, items: List[BufferedData]):
        """Return failed items to the buffer for retry."""
        async with self._lock:
            for item in items:
                item.attempts += 1
                if item.attempts < 5:  # Max 5 retries
                    buffer = self._buffers.get(item.data_type)
                    if buffer is not None:
                        buffer.appendleft(item)
    
    def _compute_available_space(self, current_size: int) -> int:
        """Compute available disk space considering max_disk_ratio."""
        try:
            total, used, free = shutil.disk_usage(self.spill_path)
            disk_reserved = int(total * (1 - self.max_disk_ratio))
            available = free - disk_reserved
            return min(self.max_spill_size, current_size + available)
        except Exception as e:
            logger.warning(f"Could not compute disk space: {e}, using max_spill_size")
            return self.max_spill_size
    
    async def _spill_to_disk(self, data_type: str) -> bool:
        """Spill buffer to disk when memory is full (Datadog-style LIFO)."""
        try:
            # Create directory with user permissions (not root)
            self.spill_path.mkdir(parents=True, exist_ok=True, mode=0o755)
            
            # Check disk space and cleanup old files if needed
            spill_files = list(self.spill_path.glob("*.json.gz"))
            current_size = sum(f.stat().st_size for f in spill_files) if spill_files else 0
            
            # Calculate how much to spill (50% of buffer by default)
            buffer = self._buffers[data_type]
            items_to_spill = int(len(buffer) * self.flush_to_disk_mem_ratio)
            items_to_spill = min(items_to_spill, 1000)  # Max 1000 items per file
            
            if items_to_spill == 0:
                return True  # Nothing to spill
            
            # Estimate size (rough estimate: ~100 bytes per item compressed)
            estimated_size = items_to_spill * 100
            
            # Check available space
            available_space = self._compute_available_space(current_size)
            
            # If we need more space, delete oldest files
            if current_size + estimated_size > available_space:
                logger.warning(
                    f"Spill directory approaching limit "
                    f"({current_size / 1024 / 1024:.1f}MB/{available_space / 1024 / 1024:.1f}MB), "
                    f"cleaning up old files..."
                )
                
                # Sort by modification time (oldest first)
                spill_files.sort(key=lambda f: f.stat().st_mtime)
                
                # Delete oldest files until we have space
                deleted_size = 0
                deleted_count = 0
                for filepath in spill_files:
                    if current_size - deleted_size + estimated_size <= available_space * 0.8:
                        break
                    try:
                        file_size = filepath.stat().st_size
                        filepath.unlink()
                        deleted_size += file_size
                        deleted_count += 1
                        self._stats["drop_count"] += 1  # Count as dropped
                    except Exception as e:
                        logger.warning(f"Failed to delete old spill file {filepath}: {e}")
                
                if deleted_count > 0:
                    logger.info(
                        f"Deleted {deleted_count} old spill files "
                        f"({deleted_size / 1024 / 1024:.1f}MB) to make room"
                    )
                
                # Recalculate size after cleanup
                current_size = sum(f.stat().st_size for f in self.spill_path.glob("*.json.gz"))
            
            # Check again if we still have space
            if current_size + estimated_size > available_space:
                logger.error(
                    f"Spill directory still full after cleanup "
                    f"({current_size / 1024 / 1024:.1f}MB). "
                    f"This indicates data is not being sent to the API. "
                    f"Check exporter status and API connectivity. "
                    f"Dropping data to prevent disk fill."
                )
                return False
            
            # Write to disk with timestamp for LIFO ordering
            # Format: data_type_YYYY_MM_DD__HH_MM_SS_timestamp.json.gz
            timestamp = datetime.utcnow()
            filename = (
                f"{data_type}_"
                f"{timestamp.strftime('%Y_%m_%d__%H_%M_%S')}_"
                f"{timestamp.timestamp()}.json.gz"
            )
            filepath = self.spill_path / filename
            
            # Get items to spill (oldest first, so newest stay in memory)
            items = [b.payload for b in list(buffer)[:items_to_spill]]
            
            if not items:
                return True  # Nothing to spill
            
            with gzip.open(filepath, "wt") as f:
                json.dump(items, f)
            
            # Clear spilled items from memory
            for _ in range(len(items)):
                if buffer:
                    buffer.popleft()
            
            self._stats["spill_count"] += 1
            actual_size = filepath.stat().st_size
            logger.info(
                f"Spilled {len(items)} {data_type} items to {filepath.name} "
                f"({actual_size / 1024:.1f}KB)"
            )
            return True
            
        except (PermissionError, OSError) as e:
            # Permission errors are expected if directory is not writable
            # Log as warning instead of error to reduce noise
            logger.warning(f"Could not spill to disk (permission issue): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to spill to disk: {e}")
            return False
    
    async def recover_from_disk(self, max_files: int = 10) -> int:
        """
        Recover spilled data from disk (LIFO - newest first, like Datadog).
        
        Args:
            max_files: Maximum number of files to recover in one call
                      (prevents memory spikes when API is down)
        
        Returns:
            Number of items recovered
        """
        if not self.spill_path.exists():
            return 0
        
        spill_files = sorted(
            self.spill_path.glob("*.json.gz"),
            key=lambda f: f.stat().st_mtime,
            reverse=True  # Newest first (LIFO)
        )
        
        if not spill_files:
            return 0
        
        recovered = 0
        files_processed = 0
        
        # Process files in reverse order (newest first) - LIFO like Datadog
        for filepath in spill_files[:max_files]:
            try:
                # Extract data type from filename (format: data_type_YYYY_MM_DD__...)
                parts = filepath.stem.split("_")
                data_type = parts[0] if parts else "metrics"
                
                with gzip.open(filepath, "rt") as f:
                    items = json.load(f)
                
                # Add items back to buffer
                for item in items:
                    if await self.add(data_type, item):
                        recovered += 1
                    else:
                        # Buffer is full, stop recovering
                        logger.warning(
                            f"Buffer full, stopping recovery. "
                            f"Recovered {recovered} items from {files_processed + 1} files. "
                            f"Remaining files: {len(spill_files) - files_processed - 1}"
                        )
                        # Don't delete this file, we'll try again later
                        return recovered
                
                # Delete recovered file only after successful recovery
                filepath.unlink()
                files_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to recover {filepath}: {e}")
                # Try to delete corrupted file
                try:
                    filepath.unlink()
                except Exception:
                    pass
        
        if recovered > 0:
            logger.info(
                f"Recovered {recovered} items from {files_processed} files "
                f"(remaining: {len(spill_files) - files_processed})"
            )
        
        return recovered
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            **self._stats,
            "buffer_sizes": {
                dtype: len(buf) for dtype, buf in self._buffers.items()
            },
        }
    
    @property
    def total_size(self) -> int:
        """Get total items in buffer."""
        return sum(len(buf) for buf in self._buffers.values())
