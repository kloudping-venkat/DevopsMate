"""
Retry strategies for forwarder.
Similar to Datadog's retry logic with exponential backoff and jitter.
"""

import asyncio
import random
import logging
from typing import Optional, Callable, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class RetryStrategy(ABC):
    """Base class for retry strategies."""
    
    @abstractmethod
    async def should_retry(self, attempt: int, error: Optional[Exception] = None, status_code: Optional[int] = None) -> bool:
        """Determine if we should retry."""
        pass
    
    @abstractmethod
    async def get_delay(self, attempt: int) -> float:
        """Get delay before next retry attempt."""
        pass


class ExponentialBackoffWithJitter(RetryStrategy):
    """
    Exponential backoff with jitter retry strategy.
    
    Similar to Datadog's retry logic:
    - Exponential backoff: delay = base_delay * (2 ^ attempt)
    - Jitter: random component to prevent thundering herd
    - Max delay cap
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter_factor: float = 0.1,
        retryable_status_codes: list = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        self.retryable_status_codes = retryable_status_codes or [429, 500, 502, 503, 504]
    
    async def should_retry(self, attempt: int, error: Optional[Exception] = None, status_code: Optional[int] = None) -> bool:
        """Determine if we should retry."""
        if attempt >= self.max_retries:
            return False
        
        # Retry on retryable status codes
        if status_code and status_code in self.retryable_status_codes:
            return True
        
        # Retry on connection errors
        if error and isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # Don't retry on client errors (4xx except 429)
        if status_code and 400 <= status_code < 500 and status_code != 429:
            return False
        
        return True
    
    async def get_delay(self, attempt: int) -> float:
        """
        Get delay with exponential backoff and jitter.
        
        Formula: delay = min(base_delay * (2 ^ attempt) + jitter, max_delay)
        """
        # Exponential backoff
        delay = self.base_delay * (2 ** attempt)
        
        # Add jitter (random component)
        jitter = delay * self.jitter_factor * random.random()
        delay += jitter
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        return delay


class FixedDelayRetry(RetryStrategy):
    """Fixed delay retry strategy."""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay
    
    async def should_retry(self, attempt: int, error: Optional[Exception] = None, status_code: Optional[int] = None) -> bool:
        return attempt < self.max_retries
    
    async def get_delay(self, attempt: int) -> float:
        return self.delay
