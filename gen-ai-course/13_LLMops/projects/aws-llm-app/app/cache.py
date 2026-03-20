"""Redis cache for LLM responses (backed by AWS ElastiCache)."""
import hashlib
import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _key(messages: list[dict], max_tokens: int) -> str:
    payload = json.dumps({"messages": messages, "max_tokens": max_tokens}, sort_keys=True)
    return "llm:v1:" + hashlib.sha256(payload.encode()).hexdigest()


class Cache:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def _conn(self) -> aioredis.Redis:
        if not self._client:
            self._client = aioredis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
        return self._client

    async def get(self, messages: list[dict], max_tokens: int) -> Optional[dict]:
        try:
            v = await (await self._conn()).get(_key(messages, max_tokens))
            return json.loads(v) if v else None
        except Exception as e:
            logger.warning("Cache get failed", extra={"error": str(e)})
            return None

    async def set(self, messages: list[dict], max_tokens: int, value: dict) -> None:
        try:
            await (await self._conn()).setex(_key(messages, max_tokens), settings.cache_ttl_seconds, json.dumps(value))
        except Exception as e:
            logger.warning("Cache set failed", extra={"error": str(e)})

    async def close(self):
        if self._client:
            await self._client.aclose()


cache = Cache()
