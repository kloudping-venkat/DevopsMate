"""Data buffer for the agent with persistence support."""

import asyncio
import json
import logging
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
    ):
        self.max_size = max_size
        self.flush_interval = flush_interval
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
    
    async def _spill_to_disk(self, data_type: str) -> bool:
        """Spill buffer to disk when memory is full."""
        try:
            # Create directory with user permissions (not root)
            self.spill_path.mkdir(parents=True, exist_ok=True, mode=0o755)
            
            # Check disk space and cleanup old files if needed
            spill_files = list(self.spill_path.glob("*.json.gz"))
            current_size = sum(f.stat().st_size for f in spill_files)
            
            # If directory is full, delete oldest files to make space
            if current_size >= self.max_spill_size:
                logger.warning(f"Spill directory full ({current_size / 1024 / 1024:.1f}MB), cleaning up old files...")
                
                # Sort by modification time (oldest first)
                spill_files.sort(key=lambda f: f.stat().st_mtime)
                
                # Delete oldest files until we have space
                deleted_size = 0
                deleted_count = 0
                for filepath in spill_files:
                    if current_size - deleted_size < self.max_spill_size * 0.8:  # Keep 20% free
                        break
                    try:
                        file_size = filepath.stat().st_size
                        filepath.unlink()
                        deleted_size += file_size
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete old spill file {filepath}: {e}")
                
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} old spill files ({deleted_size / 1024 / 1024:.1f}MB)")
                
                # Recalculate size after cleanup
                current_size = sum(f.stat().st_size for f in self.spill_path.glob("*.json.gz"))
                
                # If still full after cleanup, we have a problem - data is not being sent
                if current_size >= self.max_spill_size:
                    logger.error(
                        f"Spill directory still full after cleanup. "
                        f"This indicates data is not being sent to the API. "
                        f"Check exporter status and API connectivity. "
                        f"Dropping data to prevent disk fill."
                    )
                    return False
            
            # Write to disk
            filename = f"{data_type}_{datetime.utcnow().timestamp()}.json.gz"
            filepath = self.spill_path / filename
            
            buffer = self._buffers[data_type]
            items = [b.payload for b in list(buffer)[:1000]]
            
            if not items:
                return True  # Nothing to spill
            
            with gzip.open(filepath, "wt") as f:
                json.dump(items, f)
            
            # Clear spilled items from memory
            for _ in range(len(items)):
                if buffer:
                    buffer.popleft()
            
            self._stats["spill_count"] += 1
            logger.info(f"Spilled {len(items)} {data_type} items to {filepath} ({filepath.stat().st_size / 1024:.1f}KB)")
            return True
            
        except (PermissionError, OSError) as e:
            # Permission errors are expected if directory is not writable
            # Log as warning instead of error to reduce noise
            logger.warning(f"Could not spill to disk (permission issue): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to spill to disk: {e}")
            return False
    
    async def recover_from_disk(self) -> int:
        """Recover spilled data from disk."""
        if not self.spill_path.exists():
            return 0
        
        recovered = 0
        for filepath in sorted(self.spill_path.glob("*.json.gz")):
            try:
                data_type = filepath.stem.split("_")[0]
                
                with gzip.open(filepath, "rt") as f:
                    items = json.load(f)
                
                for item in items:
                    await self.add(data_type, item)
                    recovered += 1
                
                # Delete recovered file
                filepath.unlink()
                
            except Exception as e:
                logger.error(f"Failed to recover {filepath}: {e}")
        
        logger.info(f"Recovered {recovered} items from disk")
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
