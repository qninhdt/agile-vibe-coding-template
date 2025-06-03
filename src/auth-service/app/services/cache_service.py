import redis
from typing import Any, Optional
from omegaconf import DictConfig


class CacheService:
    """Cache service for storing and retrieving data."""

    def __init__(self, config: DictConfig):
        self.redis_client = redis.from_url(config.url, decode_responses=True)

    def add_to_sorted_set(self, key: str, value: str, score: float) -> None:
        """Add an item to a sorted set with the given score."""
        self.redis_client.zadd(key, {value: score})

    def remove_by_score_range(
        self, key: str, min_score: float, max_score: float
    ) -> int:
        """Remove items from sorted set within score range. Returns count removed."""
        return self.redis_client.zremrangebyscore(key, min_score, max_score)

    def count_sorted_set(self, key: str) -> int:
        """Get the count of items in a sorted set."""
        return self.redis_client.zcard(key)

    def set_expiration(self, key: str, seconds: int) -> None:
        """Set expiration time for a key."""
        self.redis_client.expire(key, seconds)

    def delete_key(self, key: str) -> None:
        """Delete a key from cache."""
        self.redis_client.delete(key)

    def cleanup_expired_entries(
        self, key: str, current_time: int, window_size: int
    ) -> None:
        """Clean up entries older than the window from a sorted set."""
        window_start = current_time - window_size
        self.remove_by_score_range(key, 0, window_start)

    def record_sliding_window_entry(
        self, key: str, current_time: int, window_size: int
    ) -> None:
        """Record an entry in a sliding window (sorted set) with automatic cleanup."""
        # Add current entry
        self.add_to_sorted_set(key, str(current_time), current_time)

        # Set expiration for cleanup
        self.set_expiration(key, window_size)

        # Clean old entries
        self.cleanup_expired_entries(key, current_time, window_size)

    def get_sliding_window_count(
        self, key: str, current_time: int, window_size: int
    ) -> int:
        """Get count of entries in sliding window after cleaning up expired ones."""
        self.cleanup_expired_entries(key, current_time, window_size)
        return self.count_sorted_set(key)
