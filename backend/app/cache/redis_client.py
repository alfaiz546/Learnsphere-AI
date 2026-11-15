import redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)
_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=5)
        client.ping()
        _redis_client = client
        logger.info("Redis connection established")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}. Continuing without cache.")
        return None
