"""
Redis Monitoring & Analytics
Track cache performance, hit/miss ratios, and key statistics
"""
from typing import Dict, List, Optional
import time
from datetime import datetime, timedelta
from collections import defaultdict
import json


class RedisMonitor:
    """Monitor Redis cache performance and statistics"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.stats = defaultdict(int)
        self.start_time = time.time()
    
    async def get_info(self) -> Dict:
        """Get Redis server information"""
        try:
            # Access the underlying redis client
            info = await self.redis.redis.info()
            return {
                "version": info.get("redis_version"),
                "uptime_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "used_memory_peak": info.get("used_memory_peak_human"),
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "evicted_keys": info.get("evicted_keys", 0),
                "expired_keys": info.get("expired_keys", 0),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_cache_stats(self) -> Dict:
        """Calculate cache hit/miss statistics"""
        info = await self.get_info()
        
        if "error" in info:
            return info
        
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        hit_rate = (hits / total * 100) if total > 0 else 0
        miss_rate = (misses / total * 100) if total > 0 else 0
        
        return {
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "miss_rate_percent": round(miss_rate, 2),
            "evicted_keys": info.get("evicted_keys", 0),
            "expired_keys": info.get("expired_keys", 0),
        }
    
    async def get_key_statistics(self, pattern: str = "*") -> Dict:
        """Get statistics about keys matching pattern"""
        try:
            # Get all keys matching pattern using underlying redis client
            cursor = 0
            keys = []
            while True:
                cursor, batch = await self.redis.redis.scan(cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
            
            # Analyze keys by namespace
            namespaces = defaultdict(int)
            total_memory = 0
            
            for key in keys[:1000]:  # Limit to first 1000 keys for performance
                # Get namespace (part before first colon)
                namespace = key.split(':')[0] if ':' in key else 'no_namespace'
                namespaces[namespace] += 1
                
                # Get memory usage (if available)
                try:
                    memory = await self.redis.redis.memory_usage(key)
                    if memory:
                        total_memory += memory
                except:
                    pass
            
            return {
                "total_keys": len(keys),
                "sampled_keys": min(len(keys), 1000),
                "namespaces": dict(namespaces),
                "estimated_memory_bytes": total_memory,
                "estimated_memory_mb": round(total_memory / (1024 * 1024), 2),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_slow_log(self, count: int = 10) -> List[Dict]:
        """Get slow log entries"""
        try:
            slow_log = await self.redis.redis.slowlog_get(count)
            
            entries = []
            for entry in slow_log:
                entries.append({
                    "id": entry.get("id"),
                    "timestamp": datetime.fromtimestamp(entry.get("start_time", 0)).isoformat(),
                    "duration_microseconds": entry.get("duration", 0),
                    "duration_ms": round(entry.get("duration", 0) / 1000, 2),
                    "command": " ".join([str(c) for c in entry.get("command", [])]),
                })
            
            return entries
        except Exception as e:
            return [{"error": str(e)}]
    
    async def get_memory_stats(self) -> Dict:
        """Get detailed memory statistics"""
        try:
            # Use info("memory") instead of memory_stats
            memory_info = await self.redis.redis.info("memory")
            
            return {
                "used_memory_human": memory_info.get("used_memory_human", "unknown"),
                "used_memory_peak_human": memory_info.get("used_memory_peak_human", "unknown"),
                "used_memory_rss_human": memory_info.get("used_memory_rss_human", "unknown"),
                "mem_fragmentation_ratio": memory_info.get("mem_fragmentation_ratio", 0),
                "evicted_keys": memory_info.get("evicted_keys", 0),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_comprehensive_report(self) -> Dict:
        """Get comprehensive Redis monitoring report"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "server_info": await self.get_info(),
            "cache_performance": await self.get_cache_stats(),
            "key_statistics": await self.get_key_statistics(),
            "slow_queries": await self.get_slow_log(),
            "memory_stats": await self.get_memory_stats(),
        }
    
    async def health_check(self) -> Dict:
        """Quick health check for Redis"""
        try:
            start = time.time()
            await self.redis.ping()
            latency = (time.time() - start) * 1000  # Convert to ms
            
            info = await self.get_info()
            cache_stats = await self.get_cache_stats()
            
            # Determine health status
            status = "healthy"
            warnings = []
            
            if latency > 100:
                warnings.append(f"High latency: {latency:.2f}ms")
                status = "degraded"
            
            if cache_stats.get("hit_rate_percent", 100) < 50:
                warnings.append(f"Low hit rate: {cache_stats.get('hit_rate_percent')}%")
                status = "warning"
            
            memory_used = info.get("used_memory_human", "")
            if "G" in memory_used:  # Over 1GB
                warnings.append(f"High memory usage: {memory_used}")
                status = "warning"
            
            return {
                "status": status,
                "latency_ms": round(latency, 2),
                "connected": True,
                "hit_rate": cache_stats.get("hit_rate_percent"),
                "memory": info.get("used_memory_human"),
                "warnings": warnings if warnings else None,
            }
        except Exception as e:
            return {
                "status": "down",
                "connected": False,
                "error": str(e)
            }


# FastAPI endpoint for Redis monitoring
from fastapi import APIRouter, Depends
from app.core.redis import redis_client
from app.schemas.schemas import APIResponse

router = APIRouter()


@router.get("/redis/health", response_model=APIResponse)
async def redis_health_check():
    """Quick Redis health check"""
    monitor = RedisMonitor(redis_client)
    health = await monitor.health_check()
    return APIResponse(success=True, data=health)


@router.get("/redis/stats", response_model=APIResponse)
async def redis_statistics():
    """Get Redis server statistics"""
    monitor = RedisMonitor(redis_client)
    stats = await monitor.get_info()
    return APIResponse(success=True, data=stats)


@router.get("/redis/cache-performance", response_model=APIResponse)
async def cache_performance():
    """Get cache hit/miss performance metrics"""
    monitor = RedisMonitor(redis_client)
    perf = await monitor.get_cache_stats()
    return APIResponse(success=True, data=perf)


@router.get("/redis/keys", response_model=APIResponse)
async def key_statistics(pattern: str = "*"):
    """Get key statistics by namespace"""
    monitor = RedisMonitor(redis_client)
    stats = await monitor.get_key_statistics(pattern)
    return APIResponse(success=True, data=stats)


@router.get("/redis/slow-log", response_model=APIResponse)
async def slow_log(count: int = 10):
    """Get slow query log"""
    monitor = RedisMonitor(redis_client)
    log = await monitor.get_slow_log(count)
    return APIResponse(success=True, data=log)


@router.get("/redis/report", response_model=APIResponse)
async def comprehensive_report():
    """Get comprehensive Redis monitoring report"""
    monitor = RedisMonitor(redis_client)
    report = await monitor.get_comprehensive_report()
    return APIResponse(success=True, data=report)
