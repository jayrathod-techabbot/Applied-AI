"""Semantic caching with Redis to reduce LLM calls and cost."""
import hashlib
import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _make_cache_key(messages: list[dict], max_tokens: int, temperature: float) -> str:
    """Create a deterministic cache key from request parameters."""
    payload = json.dumps(
        {"messages": messages, "max_tokens": max_tokens, "temperature": round(temperature, 2)},
        sort_keys=True,
    )
    return "llm:v1:" + hashlib.sha256(payload.encode()).hexdigest()


class LLMCache:
    """Redis-backed cache for LLM responses."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
            )
        return self._client

    async def get(self, messages: list[dict], max_tokens: int, temperature: float) -> Optional[dict]:
        """Return cached response or None."""
        try:
            client = await self._get_client()
            key = _make_cache_key(messages, max_tokens, temperature)
            value = await client.get(key)
            if value:
                logger.debug("Cache hit", extra={"key": key[:16] + "..."})
                return json.loads(value)
            logger.debug("Cache miss", extra={"key": key[:16] + "..."})
            return None
        except Exception as e:
            logger.warning("Cache get failed — falling through to LLM", extra={"error": str(e)})
            return None

    async def set(
        self,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        response: dict,
        ttl: int | None = None,
    ) -> None:
        """Store LLM response in cache."""
        try:
            client = await self._get_client()
            key = _make_cache_key(messages, max_tokens, temperature)
            ttl = ttl or settings.cache_ttl_seconds
            await client.setex(key, ttl, json.dumps(response))
            logger.debug("Cache set", extra={"key": key[:16] + "...", "ttl": ttl})
        except Exception as e:
            logger.warning("Cache set failed — continuing without cache", extra={"error": str(e)})

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton
llm_cache = LLMCache()
