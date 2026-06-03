"""Token-bucket rate limiter — caps messages per send window.

Simple, deterministic token bucket: the gateway draws one token per attempted
send; once the bucket is empty the overflow is throttled (the gateway records it
as FAILED / rate_limited). ``refill()`` resets the bucket for a new window.
"""
from __future__ import annotations


class RateLimiter:
    def __init__(self, capacity: int):
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self.capacity = capacity
        self._tokens = capacity

    @property
    def remaining(self) -> int:
        return self._tokens

    def allow(self) -> bool:
        """Consume one token. Returns True if allowed, False if throttled."""
        if self._tokens <= 0:
            return False
        self._tokens -= 1
        return True

    def refill(self) -> None:
        """Reset the bucket to full capacity (start of a new send window)."""
        self._tokens = self.capacity
