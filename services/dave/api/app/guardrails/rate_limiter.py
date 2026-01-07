"""
Rate Limiter

Tiered rate limiting to prevent abuse and control AI costs.
Supports both Redis (production) and in-memory (development) backends.
"""

import logging
import time
import threading
from dataclasses import dataclass
from typing import Optional, Dict
from collections import defaultdict

from app.config import settings

logger = logging.getLogger(__name__)

# Redis client (lazy-loaded)
_redis_client = None
_redis_lock = threading.Lock()


@dataclass
class GuardrailResult:
    """Result of guardrail check."""

    blocked: bool
    reason: Optional[str] = None
    message: Optional[str] = None
    severity: str = "low"
    detected_topic: Optional[str] = None


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a tier."""

    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int
    tokens_per_day: int


def _get_redis_client():
    """Get or create Redis client (thread-safe singleton)."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    with _redis_lock:
        if _redis_client is not None:
            return _redis_client

        if not settings.redis_url:
            return None

        try:
            import redis
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis rate limiter connected successfully")
            return _redis_client
        except Exception as e:
            logger.warning(f"Redis connection failed, falling back to in-memory: {e}")
            return None


class RateLimiter:
    """
    Rate limiter with tiered limits.

    Uses Redis for distributed rate limiting in production.
    Falls back to in-memory for development or if Redis is unavailable.

    Tiers:
    - free: 5 req/min, 100 req/day
    - basic: 15 req/min, 500 req/day
    - premium: 30 req/min, 2000 req/day
    - admin: 100 req/min, 10000 req/day
    """

    TIER_LIMITS = {
        "free": RateLimitConfig(
            requests_per_minute=5,
            requests_per_day=100,
            tokens_per_minute=1000,
            tokens_per_day=10000,
        ),
        "basic": RateLimitConfig(
            requests_per_minute=15,
            requests_per_day=500,
            tokens_per_minute=5000,
            tokens_per_day=50000,
        ),
        "premium": RateLimitConfig(
            requests_per_minute=30,
            requests_per_day=2000,
            tokens_per_minute=15000,
            tokens_per_day=150000,
        ),
        "admin": RateLimitConfig(
            requests_per_minute=100,
            requests_per_day=10000,
            tokens_per_minute=50000,
            tokens_per_day=500000,
        ),
    }

    def __init__(self):
        self._minute_window = 60
        self._day_window = 86400  # 24 hours

        # In-memory fallback storage with TTL tracking
        self._memory_lock = threading.Lock()
        self._requests: Dict[str, list] = defaultdict(list)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Clean up every 5 minutes

    @property
    def _redis(self):
        """Get Redis client (may return None if not configured)."""
        return _get_redis_client()

    @property
    def is_distributed(self) -> bool:
        """Check if using distributed (Redis) rate limiting."""
        return self._redis is not None

    def _get_key(self, user_id: Optional[str], ip_address: Optional[str]) -> str:
        """Get rate limit key for user/IP."""
        if user_id:
            return f"ratelimit:user:{user_id}"
        elif ip_address:
            return f"ratelimit:ip:{ip_address}"
        else:
            return "ratelimit:anonymous"

    def _cleanup_stale_entries(self):
        """Periodically clean up stale entries from in-memory storage."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        with self._memory_lock:
            if now - self._last_cleanup < self._cleanup_interval:
                return

            cutoff = now - self._day_window
            keys_to_remove = []

            for key, requests in self._requests.items():
                # Filter old requests
                self._requests[key] = [(ts, tokens) for ts, tokens in requests if ts > cutoff]
                # Mark empty keys for removal
                if not self._requests[key]:
                    keys_to_remove.append(key)

            # Remove empty keys to prevent memory leak
            for key in keys_to_remove:
                del self._requests[key]

            self._last_cleanup = now
            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} stale rate limit entries")

    def _clean_old_requests(self, key: str, window: int) -> list:
        """Remove requests older than window and return remaining."""
        now = time.time()
        cutoff = now - window

        with self._memory_lock:
            self._requests[key] = [
                (ts, tokens) for ts, tokens in self._requests[key]
                if ts > cutoff
            ]
            return list(self._requests[key])

    async def check(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tier: str = "free",
    ) -> GuardrailResult:
        """
        Check if request is within rate limits.

        Args:
            user_id: Optional user ID
            ip_address: Optional IP address
            tier: User tier for limit thresholds

        Returns:
            GuardrailResult with blocked=True if rate limited
        """
        if not settings.rate_limit_enabled:
            return GuardrailResult(blocked=False)

        key = self._get_key(user_id, ip_address)
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])

        # Use Redis if available, otherwise fall back to in-memory
        if self._redis:
            return await self._check_redis(key, limits)
        else:
            return await self._check_memory(key, limits)

    async def _check_redis(self, key: str, limits: RateLimitConfig) -> GuardrailResult:
        """Check rate limits using Redis."""
        try:
            redis = self._redis
            now = int(time.time())

            # Use Redis sorted sets for efficient windowed counting
            minute_key = f"{key}:minute"
            day_key = f"{key}:day"

            # Clean old entries and count in one pipeline
            pipe = redis.pipeline()

            # Remove entries older than windows
            pipe.zremrangebyscore(minute_key, 0, now - self._minute_window)
            pipe.zremrangebyscore(day_key, 0, now - self._day_window)

            # Count current entries
            pipe.zcard(minute_key)
            pipe.zcard(day_key)

            results = pipe.execute()
            request_count_minute = results[2]
            request_count_day = results[3]

            # Check minute limit
            if request_count_minute >= limits.requests_per_minute:
                return GuardrailResult(
                    blocked=True,
                    reason="rate_limit_minute",
                    message=(
                        "You've sent several messages quickly. "
                        "Please wait a moment before your next message. "
                        "I'm still here to help!"
                    ),
                    severity="low",
                )

            # Check day limit
            if request_count_day >= limits.requests_per_day:
                return GuardrailResult(
                    blocked=True,
                    reason="rate_limit_day",
                    message=(
                        "You've reached your daily message limit. "
                        "Please come back tomorrow, or consider upgrading "
                        "for more conversations. I look forward to helping you more!"
                    ),
                    severity="medium",
                )

            return GuardrailResult(blocked=False)

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fall back to allowing the request on Redis failure
            return GuardrailResult(blocked=False)

    async def _check_memory(self, key: str, limits: RateLimitConfig) -> GuardrailResult:
        """Check rate limits using in-memory storage."""
        # Trigger periodic cleanup
        self._cleanup_stale_entries()

        # Check minute window
        minute_requests = self._clean_old_requests(key, self._minute_window)
        request_count_minute = len(minute_requests)

        if request_count_minute >= limits.requests_per_minute:
            return GuardrailResult(
                blocked=True,
                reason="rate_limit_minute",
                message=(
                    "You've sent several messages quickly. "
                    "Please wait a moment before your next message. "
                    "I'm still here to help!"
                ),
                severity="low",
            )

        # Check day window
        day_requests = self._clean_old_requests(key, self._day_window)
        request_count_day = len(day_requests)

        if request_count_day >= limits.requests_per_day:
            return GuardrailResult(
                blocked=True,
                reason="rate_limit_day",
                message=(
                    "You've reached your daily message limit. "
                    "Please come back tomorrow, or consider upgrading "
                    "for more conversations. I look forward to helping you more!"
                ),
                severity="medium",
            )

        # Check token limits
        tokens_minute = sum(t for _, t in minute_requests)
        if tokens_minute >= limits.tokens_per_minute:
            return GuardrailResult(
                blocked=True,
                reason="token_limit_minute",
                message=(
                    "I've been doing a lot of thinking for you! "
                    "Let's take a brief pause. Try again in a minute."
                ),
                severity="low",
            )

        return GuardrailResult(blocked=False)

    async def record_request(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tokens_used: int = 0,
    ):
        """Record a request for rate limiting."""
        key = self._get_key(user_id, ip_address)

        if self._redis:
            await self._record_redis(key, tokens_used)
        else:
            await self._record_memory(key, tokens_used)

    async def _record_redis(self, key: str, tokens_used: int):
        """Record request in Redis."""
        try:
            redis = self._redis
            now = int(time.time())

            minute_key = f"{key}:minute"
            day_key = f"{key}:day"

            # Use pipeline for atomic operations
            pipe = redis.pipeline()

            # Add current request (use timestamp as score, unique ID as member)
            request_id = f"{now}:{tokens_used}:{id(self)}"
            pipe.zadd(minute_key, {request_id: now})
            pipe.zadd(day_key, {request_id: now})

            # Set TTLs to auto-cleanup
            pipe.expire(minute_key, self._minute_window + 10)
            pipe.expire(day_key, self._day_window + 60)

            pipe.execute()

        except Exception as e:
            logger.error(f"Redis record request failed: {e}")

    async def _record_memory(self, key: str, tokens_used: int):
        """Record request in memory."""
        with self._memory_lock:
            self._requests[key].append((time.time(), tokens_used))

    def get_usage(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tier: str = "free",
    ) -> dict:
        """Get current usage statistics."""
        key = self._get_key(user_id, ip_address)
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])

        if self._redis:
            return self._get_usage_redis(key, limits)
        else:
            return self._get_usage_memory(key, limits)

    def _get_usage_redis(self, key: str, limits: RateLimitConfig) -> dict:
        """Get usage from Redis."""
        try:
            redis = self._redis
            now = int(time.time())

            minute_key = f"{key}:minute"
            day_key = f"{key}:day"

            pipe = redis.pipeline()
            pipe.zremrangebyscore(minute_key, 0, now - self._minute_window)
            pipe.zremrangebyscore(day_key, 0, now - self._day_window)
            pipe.zcard(minute_key)
            pipe.zcard(day_key)
            results = pipe.execute()

            return {
                "requests_minute": results[2],
                "requests_minute_limit": limits.requests_per_minute,
                "requests_day": results[3],
                "requests_day_limit": limits.requests_per_day,
                "tokens_minute": 0,  # Not tracked in Redis for simplicity
                "tokens_minute_limit": limits.tokens_per_minute,
                "distributed": True,
            }
        except Exception as e:
            logger.error(f"Redis get usage failed: {e}")
            return self._get_usage_memory(key, limits)

    def _get_usage_memory(self, key: str, limits: RateLimitConfig) -> dict:
        """Get usage from memory."""
        minute_requests = self._clean_old_requests(key, self._minute_window)
        day_requests = self._clean_old_requests(key, self._day_window)

        return {
            "requests_minute": len(minute_requests),
            "requests_minute_limit": limits.requests_per_minute,
            "requests_day": len(day_requests),
            "requests_day_limit": limits.requests_per_day,
            "tokens_minute": sum(t for _, t in minute_requests),
            "tokens_minute_limit": limits.tokens_per_minute,
            "distributed": False,
        }
