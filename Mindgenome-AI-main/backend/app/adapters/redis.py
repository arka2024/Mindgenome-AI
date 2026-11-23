from __future__ import annotations

import time
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class RedisRateLimiter:
    def __init__(self) -> None:
        self.redis_url = settings.REDIS_URL
        self._client: aioredis.Redis | None = None
        self._in_memory_store: dict[str, list[float]] = {}

    async def get_client(self) -> aioredis.Redis | None:
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                )
                await self._client.ping()
            except Exception as exc:
                logger.warning("redis_unavailable_fallback_in_memory", error=str(exc))
                self._client = None
        return self._client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Sliding-window rate limiter.
        Returns (is_allowed, remaining_requests).
        """
        now = time.time()
        client = await self.get_client()

        if client is not None:
            try:
                pipe = client.pipeline()
                pipe.zremrangebyscore(key, 0, now - window_seconds)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, window_seconds + 1)
                results = await pipe.execute()

                current_count = results[2]
                allowed = current_count <= max_requests
                remaining = max(0, max_requests - current_count)
                return allowed, remaining
            except Exception as exc:
                logger.error("redis_rate_limit_error_fallback_in_memory", error=str(exc))

        # In-memory fallback
        timestamps = self._in_memory_store.get(key, [])
        timestamps = [t for t in timestamps if t > now - window_seconds]
        timestamps.append(now)
        self._in_memory_store[key] = timestamps

        allowed = len(timestamps) <= max_requests
        remaining = max(0, max_requests - len(timestamps))
        return allowed, remaining


rate_limiter = RedisRateLimiter()
