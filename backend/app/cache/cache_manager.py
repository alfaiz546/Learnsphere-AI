import json
import logging
from typing import Any, Optional
from app.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class CacheManager:
    PREFIX = "ls"
    
    def _make_key(self, resource: str, identifier: str = "") -> str:
        if identifier:
            return f"{self.PREFIX}:{resource}:{identifier}"
        return f"{self.PREFIX}:{resource}"
    
    def get(self, resource: str, identifier: str = "") -> Optional[Any]:
        client = get_redis_client()
        if not client:
            return None
        try:
            key = self._make_key(resource, identifier)
            value = client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    def set(self, resource: str, data: Any, identifier: str = "", ttl: int = 3600) -> bool:
        client = get_redis_client()
        if not client:
            return False
        try:
            key = self._make_key(resource, identifier)
            client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, resource: str, identifier: str = "") -> bool:
        client = get_redis_client()
        if not client:
            return False
        try:
            key = self._make_key(resource, identifier)
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    def invalidate_prefix(self, prefix: str) -> int:
        client = get_redis_client()
        if not client:
            return 0
        try:
            pattern = f"{self.PREFIX}:{prefix}:*"
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
        return 0
    
    def blacklist_token(self, token: str, ttl_seconds: int) -> bool:
        """Blacklists a revoked JWT token until its natural expiration."""
        if ttl_seconds <= 0:
            return True
        client = get_redis_client()
        if not client:
            logger.warning("Redis unavailable: cannot blacklist token in distributed cache.")
            return False
        try:
            key = self._make_key("blacklisted_token", token)
            client.setex(key, ttl_seconds, "1")
            return True
        except Exception as e:
            logger.warning(f"Failed to blacklist token in Redis: {e}")
            return False

    def is_token_blacklisted(self, token: str) -> Optional[bool]:
        """Checks whether a token has been explicitly blacklisted (revoked).
        Returns:
            True: Token is confirmed blacklisted.
            False: Token is confirmed NOT blacklisted.
            None: Blacklist status is unknown because Redis is unavailable.
        """
        client = get_redis_client()
        if not client:
            logger.warning("Redis unavailable: cannot verify token revocation status.")
            return None
        try:
            key = self._make_key("blacklisted_token", token)
            return bool(client.exists(key))
        except Exception as e:
            logger.warning(f"Failed to check token blacklist in Redis: {e}")
            return None

cache = CacheManager()
