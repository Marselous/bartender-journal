from __future__ import annotations

import json
from typing import Any

from redis import asyncio as redis_async
from redis.exceptions import RedisError

from app.settings import settings

_redis: redis_async.Redis | None = None


def get_redis() -> redis_async.Redis | None:
  """Return a global Redis client or None if disabled."""
  global _redis
  if _redis is not None:
      return _redis
  if not settings.redis_url:
      return None
  _redis = redis_async.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
  return _redis


async def cache_get_json(key: str) -> Any | None:
    client = get_redis()
    if not client:
        return None
    try:
        value = await client.get(key)
    except RedisError:
        # Redis unavailable or failing; degrade gracefully to cache miss.
        return None
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception:  # noqa: BLE001
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    client = get_redis()
    if not client:
        return
    try:
        data = json.dumps(value)
    except TypeError:
        return
    try:
        await client.set(key, data, ex=ttl_seconds)
    except RedisError:
        # Ignore cache write failures
        return

