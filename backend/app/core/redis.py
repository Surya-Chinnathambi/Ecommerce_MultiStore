"""
Redis Client Configuration and Caching Utilities
"""
import redis.asyncio as redis
import json
import logging
from typing import Optional, Any
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper with caching utilities"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection pool"""
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        if not self.redis:
            return False
        try:
            if ttl:
                return await self.redis.setex(key, ttl, value)
            else:
                return await self.redis.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON from Redis"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key {key}: {e}")
        return None
    
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Serialize and set JSON in Redis"""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            logger.error(f"JSON encode error for key {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not self.redis:
            return 0
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e}")
            return 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis:
            return 0
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE pattern failed for {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter"""
        if not self.redis:
            return 0
        try:
            value = await self.redis.incrby(key, amount)
            if ttl and value == amount:  # Set TTL only on first increment
                await self.redis.expire(key, ttl)
            return value
        except Exception as e:
            logger.error(f"Redis INCREMENT failed for key {key}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")


# Global Redis client instance
redis_client = RedisClient()


# Cache key generators
class CacheKeys:
    """Standardized cache key generation"""
    
    @staticmethod
    def store_products(store_id: str) -> str:
        return f"store:{store_id}:products:all"
    
    @staticmethod
    def product(store_id: str, product_id: str) -> str:
        return f"store:{store_id}:product:{product_id}"
    
    @staticmethod
    def inventory(store_id: str, product_id: str) -> str:
        return f"store:{store_id}:inventory:{product_id}"
    
    @staticmethod
    def store_config(store_id: str) -> str:
        return f"store:{store_id}:config"
    
    @staticmethod
    def categories(store_id: str) -> str:
        return f"store:{store_id}:categories"
    
    @staticmethod
    def rate_limit(store_id: str, endpoint: str, minute: int) -> str:
        return f"ratelimit:{store_id}:{endpoint}:{minute}"
    
    @staticmethod
    def session(session_id: str) -> str:
        return f"session:{session_id}"
    
    @staticmethod
    def cart(session_id: str) -> str:
        return f"cart:{session_id}"


# Decorator for caching function results
def cached(ttl: int, key_func=None):
    """
    Decorator to cache function results in Redis
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from args
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = await redis_client.get_json(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.set_json(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
