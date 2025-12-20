"""Rate limiting service."""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import redis
from ..config import config


class RateLimiter:
    """Rate limiting with Redis backend."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or config.redis_url
        self.redis_client = None
        self.use_redis = bool(self.redis_url)
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
            except Exception:
                self.use_redis = False
                self.redis_client = None
        
        # Fallback to in-memory storage
        if not self.use_redis:
            self.memory_store: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def check_rate_limit(self, identifier: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        Returns: (allowed, remaining, reset_time)
        """
        if self.use_redis:
            return self._check_redis_rate_limit(identifier, limit, window)
        else:
            return self._check_memory_rate_limit(identifier, limit, window)
    
    def _check_redis_rate_limit(self, identifier: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """Check rate limit using Redis."""
        if not self.redis_client:
            return True, limit, int(time.time()) + window
        
        key = f"rate_limit:{identifier}"
        now = int(time.time())
        
        # Use sliding window log algorithm
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        results = pipe.execute()
        
        current_count = results[1] + 1  # +1 for current request
        allowed = current_count <= limit
        remaining = max(0, limit - current_count)
        reset_time = now + window
        
        return allowed, remaining, reset_time
    
    def _check_memory_rate_limit(self, identifier: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """Check rate limit using in-memory storage."""
        now = int(time.time())
        cutoff = now - window
        
        # Get or create entry
        entry = self.memory_store[identifier]
        timestamps = entry.get("timestamps", [])
        
        # Remove old timestamps
        timestamps = [ts for ts in timestamps if ts > cutoff]
        
        # Add current request
        timestamps.append(now)
        entry["timestamps"] = timestamps
        entry["last_check"] = now
        
        current_count = len(timestamps)
        allowed = current_count <= limit
        remaining = max(0, limit - current_count)
        reset_time = now + window
        
        return allowed, remaining, reset_time
    
    def check_ip_rate_limit(self, ip_address: str) -> Tuple[bool, int, int]:
        """Check rate limit for IP address."""
        return self.check_rate_limit(
            identifier=f"ip:{ip_address}",
            limit=config.rate_limit_per_ip,
            window=config.rate_limit_window
        )
    
    def check_user_rate_limit(self, user_id: int) -> Tuple[bool, int, int]:
        """Check rate limit for user."""
        return self.check_rate_limit(
            identifier=f"user:{user_id}",
            limit=config.rate_limit_per_user,
            window=config.rate_limit_window
        )
    
    def check_endpoint_rate_limit(self, endpoint: str, ip_address: str) -> Tuple[bool, int, int]:
        """Check rate limit for specific endpoint."""
        # Get endpoint-specific limit or use default
        limit = config.rate_limit_per_endpoint.get(endpoint, config.rate_limit_per_ip)
        
        return self.check_rate_limit(
            identifier=f"endpoint:{endpoint}:{ip_address}",
            limit=limit,
            window=config.rate_limit_window
        )
    
    def cleanup_old_entries(self):
        """Clean up old rate limit entries."""
        if not self.use_redis:
            # Clean up in-memory store
            now = int(time.time())
            for identifier in list(self.memory_store.keys()):
                entry = self.memory_store[identifier]
                last_check = entry.get("last_check", 0)
                
                # Remove entries older than 1 hour
                if now - last_check > 3600:
                    del self.memory_store[identifier]



