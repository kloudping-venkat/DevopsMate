"""
Collector package - check interface and scheduler.
Similar to Datadog's pkg/collector structure.
"""

from .check import Check, CheckResult
from .scheduler import Scheduler, Job

__all__ = ["Check", "CheckResult", "Scheduler", "Job"]
