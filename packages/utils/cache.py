import json
import hashlib
import functools
from typing import Callable, Optional
from fastapi import Request

from packages.utils.logger import get_logger

logger = get_logger(__name__)


def cached(ttl: int = 120, key_prefix: str = ""):
    """Decorator for caching FastAPI endpoints in Redis."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object to get Redis from app state
            request: Optional[Request] = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )

            redis = None
            if request and hasattr(request.app.state, "redis"):
                redis = request.app.state.redis

            if redis is None:
                return await func(*args, **kwargs)

            # Build cache key from prefix + kwargs hash
            key_data = {k: str(v) for k, v in kwargs.items() if k not in ("db", "request")}
            key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:8]
            cache_key = f"probalyze:{key_prefix}:{key_hash}"

            cached_value = await redis.get(cache_key)
            if cached_value:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached_value)

            result = await func(*args, **kwargs)
            await redis.setex(cache_key, ttl, json.dumps(result, default=str))
            return result

        return wrapper
    return decorator
