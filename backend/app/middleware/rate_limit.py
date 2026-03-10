"""
Rate Limiting Middleware
Implements per-store and per-IP rate limiting
"""
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

from app.core.config import settings
from app.core.redis import redis_client, CacheKeys

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting implementation
    Configurable limits per store tier and endpoint type
    """
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Determine rate limit based on endpoint
        limit, window = self.get_rate_limit(request)
        
        if limit:
            # Get identifier (IP or store_id)
            identifier = self.get_identifier(request)
            
            # Check rate limit BEFORE processing the request
            allowed, remaining, reset_time = await self.check_rate_limit(
                identifier,
                request.url.path,
                limit,
                window
            )
            
            # Return 429 immediately — do NOT call call_next when blocked
            if not allowed:
                from starlette.responses import JSONResponse as _JSONResponse
                retry_after = max(0, reset_time - int(time.time()))
                return _JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please slow down.",
                            "retry_after": retry_after,
                        },
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(retry_after),
                    },
                )
            
            # Allowed — process the request then attach headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            return response
        else:
            return await call_next(request)
    
    def get_rate_limit(self, request: Request) -> tuple:
        """
        Determine rate limit for request
        Returns: (limit, window_seconds)
        """
        path = request.url.path
        
        # Sync API - based on store tier
        if "/api/v1/sync/" in path:
            store_tier = getattr(request.state, "store_tier", "tier3")
            if store_tier == "tier1":
                return settings.RATE_LIMIT_TIER1_SYNC, 60
            elif store_tier == "tier2":
                return settings.RATE_LIMIT_TIER2_SYNC, 60
            else:
                return settings.RATE_LIMIT_TIER3_SYNC, 60
        
        # Storefront API - per IP
        elif "/api/v1/storefront/" in path:
            return settings.RATE_LIMIT_STOREFRONT, 60
        
        # Dashboard API - per session
        elif "/api/v1/dashboard/" in path:
            return settings.RATE_LIMIT_DASHBOARD, 60
        
        # No rate limit for other endpoints
        return None, None
    
    def get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (IP or store_id)"""
        # For sync API, use store_id
        if "/api/v1/sync/" in request.url.path:
            return getattr(request.state, "store_id", "unknown")
        
        # For storefront, use IP address
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """Collapse dynamic IDs to keep Redis key cardinality bounded."""
        normalized_parts = []
        for part in path.strip("/").split("/"):
            if not part:
                continue
            # Normalize UUID-like or numeric segments.
            if len(part) >= 16 and "-" in part:
                normalized_parts.append(":id")
                continue
            if part.isdigit():
                normalized_parts.append(":id")
                continue
            normalized_parts.append(part)
        return "/" + "/".join(normalized_parts)

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window: int
    ) -> tuple:
        """
        Check if request is within rate limit
        Returns: (allowed, remaining, reset_time)
        """
        current_minute = int(time.time() / window)
        normalized_endpoint = self._normalize_endpoint(endpoint)
        cache_key = f"ratelimit:{identifier}:{normalized_endpoint}:{current_minute}"
        
        # Increment counter
        count = await redis_client.increment(cache_key, ttl=window)
        
        # Calculate remaining and reset time
        remaining = max(0, limit - count)
        reset_time = (current_minute + 1) * window
        
        # Check if allowed
        allowed = count <= limit
        
        # Soft limit warning (at 80%)
        if count >= (limit * 0.8) and count < limit:
            logger.warning(f"Rate limit approaching for {identifier}: {count}/{limit}")
        
        return allowed, remaining, reset_time
