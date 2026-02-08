"""
Scheduler - job-based scheduling for checks.
Similar to Datadog's pkg/collector/scheduler structure.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from agent.pkg.collector.check import Check, CheckResult

logger = logging.getLogger(__name__)


@dataclass
class Job:
    """A scheduled job for running a check."""
    check: Check
    interval: float  # seconds
    instance: Optional[Dict[str, Any]] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True
    
    def __post_init__(self):
        if self.next_run is None:
            self.next_run = datetime.utcnow()


class Scheduler:
    """
    Schedules and runs checks at specified intervals.
    
    Similar to Datadog's scheduler:
    - Job-based scheduling
    - Interval management
    - Error handling
    - Stats tracking
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    def add_check(self, check: Check, interval: float, instance: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a check to the scheduler.
        
        Args:
            check: Check instance to run
            interval: Interval in seconds
            instance: Optional instance configuration
            
        Returns:
            Job ID
        """
        job_id = f"{check.name}_{id(check)}"
        job = Job(
            check=check,
            interval=interval,
            instance=instance,
        )
        self.jobs[job_id] = job
        logger.info(f"Added check '{check.name}' with interval {interval}s")
        return job_id
    
    def remove_check(self, job_id: str):
        """Remove a check from the scheduler."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Removed check '{job_id}'")
    
    def enable_check(self, job_id: str):
        """Enable a check."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
    
    def disable_check(self, job_id: str):
        """Disable a check."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")
    
    async def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._run_pending_jobs()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
    
    async def _run_pending_jobs(self):
        """Run all jobs that are due."""
        now = datetime.utcnow()
        
        for job_id, job in self.jobs.items():
            if not job.enabled:
                continue
            
            if job.next_run and now >= job.next_run:
                # Run the job
                asyncio.create_task(self._run_job(job_id, job))
    
    async def _run_job(self, job_id: str, job: Job):
        """Run a single job."""
        start_time = time.time()
        
        try:
            result = await job.check.check(job.instance)
            job.last_run = datetime.utcnow()
            job.run_count += 1
            job.next_run = job.last_run + timedelta(seconds=job.interval)
            
            if result.status == 'error':
                job.error_count += 1
            
            logger.debug(f"Check '{job.check.name}' completed in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            job.error_count += 1
            logger.error(f"Error running check '{job.check.name}': {e}")
            job.next_run = datetime.utcnow() + timedelta(seconds=job.interval)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "running": self.running,
            "jobs_count": len(self.jobs),
            "jobs": {
                job_id: {
                    "name": job.check.name,
                    "interval": job.interval,
                    "run_count": job.run_count,
                    "error_count": job.error_count,
                    "enabled": job.enabled,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "next_run": job.next_run.isoformat() if job.next_run else None,
                }
                for job_id, job in self.jobs.items()
            },
        }
