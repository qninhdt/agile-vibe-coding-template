"""Redis-based rate limiter for authentication endpoints."""

import time
from typing import Optional
import redis

from app.config import config
from app.utils.errors import RateLimitError


class RateLimiter:
    """Redis-based sliding window rate limiter."""

    def __init__(self):
        redis_url = config.get("redis.url", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.enabled = config.get("login.rate_limits.enabled", True)

        # Rate limit configurations
        self.per_ip_requests = config.get("login.rate_limits.per_ip_requests", 20)
        self.per_ip_window = (
            config.get("login.rate_limits.per_ip_window_minutes", 15) * 60
        )

        self.per_identifier_attempts = config.get(
            "login.rate_limits.per_identifier_attempts", 5
        )
        self.per_identifier_window = (
            config.get("login.rate_limits.per_identifier_window_minutes", 15) * 60
        )

        self.per_account_attempts = config.get(
            "login.rate_limits.per_account_attempts", 10
        )
        self.per_account_window = (
            config.get("login.rate_limits.per_account_window_minutes", 60) * 60
        )

    def check_rate_limit(
        self,
        ip_address: str,
        identifier: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Check rate limits for IP, identifier, and account."""
        if not self.enabled:
            return

        current_time = int(time.time())

        # Check IP rate limit
        self._check_sliding_window(
            f"ip:{ip_address}",
            current_time,
            self.per_ip_requests,
            self.per_ip_window,
            f"Too many requests from IP {ip_address}",
        )

        # Check identifier rate limit
        if identifier:
            self._check_sliding_window(
                f"identifier:{identifier}",
                current_time,
                self.per_identifier_attempts,
                self.per_identifier_window,
                f"Too many login attempts for {identifier}",
            )

        # Check account rate limit
        if user_id:
            self._check_sliding_window(
                f"account:{user_id}",
                current_time,
                self.per_account_attempts,
                self.per_account_window,
                f"Account temporarily locked due to too many failed attempts",
            )

    def record_attempt(
        self,
        ip_address: str,
        identifier: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Record an attempt for rate limiting."""
        if not self.enabled:
            return

        current_time = int(time.time())

        # Record IP attempt
        self._record_sliding_window(
            f"ip:{ip_address}", current_time, self.per_ip_window
        )

        # Record identifier attempt
        if identifier:
            self._record_sliding_window(
                f"identifier:{identifier}", current_time, self.per_identifier_window
            )

        # Record account attempt (only for failed logins)
        if user_id:
            self._record_sliding_window(
                f"account:{user_id}", current_time, self.per_account_window
            )

    def _check_sliding_window(
        self,
        key: str,
        current_time: int,
        max_requests: int,
        window_size: int,
        error_message: str,
    ) -> None:
        """Check sliding window rate limit."""
        window_start = current_time - window_size

        # Clean old entries
        self.redis_client.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        current_count = self.redis_client.zcard(key)

        if current_count >= max_requests:
            raise RateLimitError(error_message)

    def _record_sliding_window(
        self, key: str, current_time: int, window_size: int
    ) -> None:
        """Record request in sliding window."""
        # Add current request
        self.redis_client.zadd(key, {str(current_time): current_time})

        # Set expiration for cleanup
        self.redis_client.expire(key, window_size)

        # Clean old entries
        window_start = current_time - window_size
        self.redis_client.zremrangebyscore(key, 0, window_start)

    def clear_user_rate_limits(self, user_id: str) -> None:
        """Clear rate limits for a user (e.g., after successful login)."""
        self.redis_client.delete(f"account:{user_id}")

    def get_remaining_attempts(self, key_type: str, identifier: str) -> int:
        """Get remaining attempts for a rate limit key."""
        if not self.enabled:
            return 999  # Unlimited when disabled

        key = f"{key_type}:{identifier}"
        current_time = int(time.time())

        if key_type == "ip":
            window_size = self.per_ip_window
            max_requests = self.per_ip_requests
        elif key_type == "identifier":
            window_size = self.per_identifier_window
            max_requests = self.per_identifier_attempts
        elif key_type == "account":
            window_size = self.per_account_window
            max_requests = self.per_account_attempts
        else:
            return 0

        window_start = current_time - window_size
        self.redis_client.zremrangebyscore(key, 0, window_start)
        current_count = self.redis_client.zcard(key)

        return max(0, max_requests - current_count)
