"""
Rate limiter for API calls to prevent hitting rate limits.
"""

import asyncio
import functools
import random
import time
from datetime import datetime, timedelta
from typing import Awaitable, Callable, List, TypeVar

from ..utils.timestamps import get_current_timestamp

T = TypeVar("T")


class RateLimiterConfig:
    """Configuration constants for rate limiting."""

    # Default rate limits
    DEFAULT_REQUESTS_PER_MINUTE = 10
    DEFAULT_REQUESTS_PER_DAY = 1000

    # Time constants
    MINUTE_WINDOW_SECONDS = 60
    MIN_WAIT_SECONDS = 1

    # Jitter configuration
    JITTER_RANGE = 0.1  # ±10%

    # Daily reset time
    DAILY_RESET_HOUR = 0
    DAILY_RESET_MINUTE = 0


class RateLimiter:
    """
    Rate limiter for API calls to prevent hitting rate limits.
    """

    def __init__(
        self,
        requests_per_minute: int = RateLimiterConfig.DEFAULT_REQUESTS_PER_MINUTE,
        requests_per_day: int = RateLimiterConfig.DEFAULT_REQUESTS_PER_DAY,
    ):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_day: Maximum requests per day
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.request_timestamps: List[datetime] = []
        self.daily_count = 0
        self.daily_reset_time = get_current_timestamp().replace(
            hour=RateLimiterConfig.DAILY_RESET_HOUR,
            minute=RateLimiterConfig.DAILY_RESET_MINUTE,
            second=0,
            microsecond=0,
        ) + timedelta(days=1)

    def _cleanup_old_timestamps(self) -> None:
        """Remove timestamps older than 1 minute."""
        now = datetime.now()
        self.request_timestamps = [ts for ts in self.request_timestamps if (now - ts) < timedelta(minutes=1)]

        # Reset daily count if we've passed the reset time
        if now >= self.daily_reset_time:
            self.daily_count = 0
            self.daily_reset_time = now.replace(
                hour=RateLimiterConfig.DAILY_RESET_HOUR,
                minute=RateLimiterConfig.DAILY_RESET_MINUTE,
                second=0,
                microsecond=0,
            ) + timedelta(days=1)

    def should_limit(self) -> bool:
        """
        Check if the next request should be rate limited.

        Returns:
            True if request should be limited, False otherwise
        """
        self._cleanup_old_timestamps()

        # Check minute limit
        if len(self.request_timestamps) >= self.requests_per_minute:
            return True

        # Check daily limit
        if self.daily_count >= self.requests_per_day:
            return True

        return False

    def record_request(self) -> None:
        """Record a new request."""
        self._cleanup_old_timestamps()
        self.request_timestamps.append(datetime.now())
        self.daily_count += 1

    def wait_if_needed(self, jitter: bool = True) -> float:
        """
        Wait if rate limiting is needed.

        Args:
            jitter: Add random jitter to avoid thundering herd

        Returns:
            Time waited in seconds
        """
        self._cleanup_old_timestamps()

        if not self.should_limit():
            self.record_request()
            return 0.0

        # Calculate wait time
        if self.daily_count >= self.requests_per_day:
            # Need to wait until tomorrow
            wait_seconds = (self.daily_reset_time - datetime.now()).total_seconds()
            wait_seconds = max(wait_seconds, RateLimiterConfig.MIN_WAIT_SECONDS)
        else:
            # Need to wait until oldest request falls out of the window
            oldest = min(self.request_timestamps)
            wait_seconds = RateLimiterConfig.MINUTE_WINDOW_SECONDS - (datetime.now() - oldest).total_seconds()
            wait_seconds = max(wait_seconds, RateLimiterConfig.MIN_WAIT_SECONDS)

        # Add jitter if requested (±10%)
        if jitter:
            wait_seconds *= 1 + random.uniform(-RateLimiterConfig.JITTER_RANGE, RateLimiterConfig.JITTER_RANGE)

        # Wait and then record
        time.sleep(wait_seconds)
        self.record_request()
        return wait_seconds

    def limit_sync(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for rate-limiting synchronous functions.

        Args:
            func: Function to rate limit

        Returns:
            Rate-limited function
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)

        return wrapper

    def limit_async(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """
        Decorator for rate-limiting asynchronous functions.

        Args:
            func: Async function to rate limit

        Returns:
            Rate-limited async function
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            wait_time = self.wait_if_needed()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            return await func(*args, **kwargs)

        return wrapper
