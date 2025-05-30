import time
from typing import Any, Dict, Optional
from src.utils.logger import logger
from config.settings import settings

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SimpleCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry['expires']:
            del self.cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.log("Cache cleared")


class RedisCache:
    def __init__(self):
        self.fallback_cache = SimpleCache()
        self.redis_available = False
        
        if REDIS_AVAILABLE:
            try:
                self.conn = redis.Redis.from_url(settings.REDIS_URL)
                # Test connection
                self.conn.ping()
                self.redis_available = True
                logger.log("Redis cache initialized successfully")
            except Exception as e:
                logger.log(f"Redis connection failed, using in-memory cache: {e}")
        else:
            logger.log("Redis not available, using in-memory cache")

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value from cache by key."""
        if self.redis_available:
            try:
                value = self.conn.get(key)
                if value:
                    logger.log(f"Redis cache hit for key: {key}")
                    return value.decode('utf-8')
                logger.log(f"Redis cache miss for key: {key}")
                return None
            except Exception as e:
                logger.log(f"Redis error, falling back to memory cache: {e}")
                self.redis_available = False
        
        # Use fallback cache
        return self.fallback_cache.get(key)

    def set(self, key: str, value: str, ttl: int = 3600):
        """Set a value in the cache with a TTL (default: 1 hour)."""
        if self.redis_available:
            try:
                self.conn.setex(key, ttl, value)
                logger.log(f"Redis cache set for key: {key} with TTL: {ttl} seconds")
                return
            except Exception as e:
                logger.log(f"Redis error, falling back to memory cache: {e}")
                self.redis_available = False
        
        # Use fallback cache
        self.fallback_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if self.redis_available:
            try:
                result = self.conn.delete(key)
                logger.log(f"Redis cache delete for key: {key}")
                return bool(result)
            except Exception as e:
                logger.log(f"Redis error, falling back to memory cache: {e}")
                self.redis_available = False
        
        # Use fallback cache
        return self.fallback_cache.delete(key)
    
    def clear_all(self) -> None:
        """Clear all cache entries"""
        if self.redis_available:
            try:
                self.conn.flushdb()
                logger.log("Redis cache cleared")
                return
            except Exception as e:
                logger.log(f"Redis error, falling back to memory cache: {e}")
                self.redis_available = False
        
        # Use fallback cache
        self.fallback_cache.clear_all()


# Global cache instance
cache = RedisCache()