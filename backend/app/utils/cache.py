"""Simple in-memory cache for search results"""
import time
import logging
from typing import Dict, Any, Optional
import hashlib
import json

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default 1 hour)
        """
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl_seconds = ttl_seconds

    def _make_key(self, prefix: str, **kwargs) -> str:
        """
        Create cache key from prefix and kwargs

        Args:
            prefix: Key prefix
            **kwargs: Key parameters

        Returns:
            Cache key string
        """
        # Sort kwargs for consistent keys
        sorted_params = json.dumps(kwargs, sort_keys=True)
        hash_obj = hashlib.md5(sorted_params.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            return None

        value, expiry_time = self.cache[key]

        # Check if expired
        if time.time() > expiry_time:
            del self.cache[key]
            logger.debug(f"Cache expired: {key}")
            return None

        logger.debug(f"Cache hit: {key}")
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        expiry_time = time.time() + (ttl or self.ttl_seconds)
        self.cache[key] = (value, expiry_time)
        logger.debug(f"Cache set: {key}")

    def delete(self, key: str):
        """
        Delete value from cache

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if current_time > expiry
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def stats(self) -> Dict[str, int]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        current_time = time.time()
        valid_entries = sum(
            1 for _, expiry in self.cache.values()
            if current_time <= expiry
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
        }


# Global cache instance
_search_cache: Optional[SimpleCache] = None


def get_search_cache() -> SimpleCache:
    """Get or create the global search cache"""
    global _search_cache
    if _search_cache is None:
        _search_cache = SimpleCache(ttl_seconds=86400)  # 24 hour TTL
    return _search_cache
