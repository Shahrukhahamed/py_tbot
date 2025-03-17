import redis
from src.utils.logger import logger
from config.settings import settings

class RedisCache:
    def __init__(self):
        try:
            self.conn = redis.Redis.from_url(settings.REDIS_URL)
        except redis.ConnectionError as e:
            logger.log(f"Redis connection error: {e}")
            raise

    def get(self, key: str) -> str:
        """Retrieve a value from cache by key."""
        try:
            value = self.conn.get(key)
            if value:
                logger.log(f"Cache hit for key: {key}")
                return value.decode('utf-8')  # Decoding byte string to str
            logger.log(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.log(f"Error retrieving key {key} from cache: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 3600):
        """Set a value in the cache with a TTL (default: 1 hour)."""
        try:
            self.conn.setex(key, ttl, value)
            logger.log(f"Cache set for key: {key} with TTL: {ttl} seconds")
        except Exception as e:
            logger.log(f"Error setting key {key} in cache: {e}")