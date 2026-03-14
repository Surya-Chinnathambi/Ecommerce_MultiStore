"""
Tenant/Store Middleware
Identifies and validates store based on domain/subdomain
"""
from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.core.database import SessionLocal
from app.models.models import Store
from app.core.redis import redis_client, CacheKeys

logger = logging.getLogger(__name__)


def get_current_store_id(request: Request) -> UUID:
    """
    Dependency to get current store ID from request state
    Used in endpoints that require store context
    """
    if not hasattr(request.state, "store_id"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found. Please provide store_id in header or query parameter."
        )
    return UUID(request.state.store_id)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to identify store/tenant from request
    Sets store_id in request.state for downstream use
    """
    
    async def dispatch(self, request: Request, call_next):
        def _error_response(code: int, detail: str) -> JSONResponse:
            return JSONResponse(
                status_code=code,
                content={
                    "success": False,
                    "error": {
                        "code": "STORE_CONTEXT_ERROR",
                        "message": detail,
                    },
                },
            )

        # Skip middleware for health check and docs
        if request.url.path in ["/health", "/", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Extract store identifier from:
        # 1. Custom domain (mystore.com)
        # 2. Subdomain (mystore.platform.com)
        # 3. Header (X-Store-ID)
        # 4. Query param (?store_id=...)
        
        store = None
        host = request.headers.get("host", "").split(":")[0]  # Remove port
        
        # Try custom domain
        if host and not host.startswith("localhost") and not host.startswith("127.0.0.1"):
            store = await self.get_store_by_domain(host)
        
        # Try X-Store-ID header
        if store is None:
            store_id = request.headers.get("X-Store-ID")
            if store_id:
                store = await self.get_store_by_id(store_id)
        
        # Try query parameter
        if store is None:
            store_id = request.query_params.get("store_id")
            if store_id:
                store = await self.get_store_by_id(store_id)
        
        # For sync API, store_id is in request body (handled by endpoint)
        # Skip validation for sync endpoints
        if "/sync/" in request.url.path:
            return await call_next(request)
        
        # Validate store found and active
        if store is not None:
            if not store.is_active:
                return _error_response(status.HTTP_403_FORBIDDEN, "Store is not active")
            
            # Set store in request state
            request.state.store = store
            request.state.store_id = str(store.id)
        else:
            # For public endpoints without store, use default store
            if self.is_public_endpoint(request.url.path):
                # Get first active store as default
                default_store = await self.get_default_store()
                if default_store is not None:
                    request.state.store = default_store
                    request.state.store_id = str(default_store.id)
            else:
                # Strictly require store for non-public endpoints
                return _error_response(status.HTTP_404_NOT_FOUND, "Store not found")
        
        response = await call_next(request)
        return response
    
    async def get_default_store(self) -> Store:
        """Get first active store as default"""
        cache_key = "store:default"
        
        # Check cache
        cached_store = await redis_client.get_json(cache_key)
        if cached_store:
            if "is_active" not in cached_store:
                # Legacy cache payloads can miss fields required by middleware.
                await redis_client.delete(cache_key)
            else:
                return Store(**cached_store)
        
        # Query database
        db = SessionLocal()
        try:
            store = db.query(Store).filter(Store.is_active == True).first()
            if store is not None:
                store_dict = {
                    "id": str(store.id),
                    "name": store.name,
                    "domain": store.domain,
                    "is_active": store.is_active,
                    "status": store.status
                }
                await redis_client.set_json(cache_key, store_dict, ttl=3600)
            return store
        finally:
            db.close()
    
    async def get_store_by_domain(self, domain: str) -> Store:
        """Get store by custom domain with caching"""
        cache_key = f"store:domain:{domain}"
        
        # Check cache
        cached_store = await redis_client.get_json(cache_key)
        if cached_store:
            if "is_active" not in cached_store:
                await redis_client.delete(cache_key)
            else:
                return Store(**cached_store)
        
        # Query database
        db = SessionLocal()
        try:
            store = db.query(Store).filter(Store.domain == domain).first()
            if store is not None:
                # Cache for 1 hour
                store_dict = {
                    "id": str(store.id),
                    "name": store.name,
                    "domain": store.domain,
                    "is_active": store.is_active,
                    "status": store.status
                }
                await redis_client.set_json(cache_key, store_dict, ttl=3600)
            return store
        finally:
            db.close()
    
    async def get_store_by_id(self, store_id: str) -> Store:
        """Get store by ID with caching"""
        cache_key = CacheKeys.store_config(store_id)
        
        # Check cache
        cached_store = await redis_client.get_json(cache_key)
        if cached_store:
            if "is_active" not in cached_store:
                await redis_client.delete(cache_key)
            else:
                return Store(**cached_store)
        
        # Query database
        db = SessionLocal()
        try:
            store = db.query(Store).filter(Store.id == store_id).first()
            if store is not None:
                store_dict = {
                    "id": str(store.id),
                    "name": store.name,
                    "domain": store.domain,
                    "is_active": store.is_active,
                    "status": store.status
                }
                await redis_client.set_json(cache_key, store_dict, ttl=3600)
            return store
        finally:
            db.close()
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require store)"""
        public_paths = [
            "/api/v1/auth/",
            "/api/v1/admin/",
            "/api/v1/products",
            "/api/v1/stores",
            "/api/v1/storefront/",
            "/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/"
        ]
        return any(path.startswith(p) for p in public_paths)
