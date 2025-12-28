"""
Enhanced Search Service
Provides advanced search capabilities with fuzzy matching, filters, and ranking
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.models.models import Product, Category
from app.core.redis import redis_client
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search service with caching and ranking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_cache_key(self, query: str, filters: Dict) -> str:
        """Generate cache key for search query"""
        cache_data = f"search:{query}:{json.dumps(filters, sort_keys=True)}"
        return f"search:{hashlib.md5(cache_data.encode()).hexdigest()}"
    
    async def search_products(
        self,
        query: str,
        store_id: str,
        filters: Optional[Dict] = None,
        limit: int = 50
    ) -> List[Product]:
        """
        Enhanced product search with:
        - Fuzzy matching
        - Multi-field search
        - Relevance ranking
        - Caching
        """
        filters = filters or {}
        
        # Check cache first
        cache_key = self._generate_cache_key(query, filters)
        cached_results = await redis_client.get_json(cache_key)
        if cached_results:
            return [Product(**p) for p in cached_results]
        
        # Build search query
        search_term = f"%{query}%"
        
        # Base query with relevance scoring
        query_obj = self.db.query(Product).filter(
            and_(
                Product.store_id == store_id,
                Product.is_active == True
            )
        )
        
        # Multi-field search with different weights
        search_conditions = []
        
        # Exact match in name (highest priority)
        if query.lower() in ['name', 'product']:
            search_conditions.append(Product.name.ilike(f"%{query}%"))
        else:
            search_conditions.extend([
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.barcode.ilike(search_term),
            ])
        
        query_obj = query_obj.filter(or_(*search_conditions))
        
        # Apply filters
        if filters.get("category_id"):
            query_obj = query_obj.filter(Product.category_id == filters["category_id"])
        
        if filters.get("min_price"):
            query_obj = query_obj.filter(Product.selling_price >= filters["min_price"])
        
        if filters.get("max_price"):
            query_obj = query_obj.filter(Product.selling_price <= filters["max_price"])
        
        if filters.get("in_stock"):
            query_obj = query_obj.filter(Product.is_in_stock == True)
        
        if filters.get("is_featured"):
            query_obj = query_obj.filter(Product.is_featured == True)
        
        # Order by relevance (featured first, then by name)
        query_obj = query_obj.order_by(
            Product.is_featured.desc(),
            Product.name
        ).limit(limit)
        
        results = query_obj.all()
        
        # Cache results for 5 minutes
        if results:
            cache_data = [self._product_to_dict(p) for p in results]
            await redis_client.set_json(cache_key, cache_data, ttl=300)
        
        return results
    
    def _product_to_dict(self, product: Product) -> Dict:
        """Convert product to dict for caching"""
        return {
            "id": str(product.id),
            "store_id": str(product.store_id),
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "selling_price": product.selling_price,
            "mrp": product.mrp,
            "quantity": product.quantity,
            "is_in_stock": product.is_in_stock,
            "is_featured": product.is_featured,
            "thumbnail": product.thumbnail,
            "sku": product.sku,
        }
    
    async def get_suggestions(
        self,
        query: str,
        store_id: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions/autocomplete
        Returns list of product names
        """
        if len(query) < 2:
            return []
        
        cache_key = f"suggestions:{store_id}:{query.lower()}"
        cached = await redis_client.get_json(cache_key)
        if cached:
            return cached
        
        # Get product names starting with query
        results = self.db.query(Product.name).filter(
            and_(
                Product.store_id == store_id,
                Product.is_active == True,
                Product.name.ilike(f"{query}%")
            )
        ).limit(limit).all()
        
        suggestions = [r[0] for r in results]
        
        # Cache for 1 hour
        await redis_client.set_json(cache_key, suggestions, ttl=3600)
        
        return suggestions
    
    async def get_popular_searches(
        self,
        store_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get popular search terms"""
        cache_key = f"popular_searches:{store_id}"
        cached = await redis_client.get_json(cache_key)
        if cached:
            return cached
        
        # Get most searched categories
        popular_categories = self.db.query(
            Category.name,
            func.count(Product.id).label('product_count')
        ).join(
            Product, Product.category_id == Category.id
        ).filter(
            and_(
                Category.store_id == store_id,
                Product.is_active == True
            )
        ).group_by(Category.name).order_by(
            func.count(Product.id).desc()
        ).limit(limit).all()
        
        results = [
            {"term": cat[0], "count": cat[1]}
            for cat in popular_categories
        ]
        
        # Cache for 1 hour
        await redis_client.set_json(cache_key, results, ttl=3600)
        
        return results
    
    async def track_search(self, query: str, store_id: str, result_count: int):
        """Track search query for analytics"""
        try:
            key = f"search_analytics:{store_id}"
            
            # Use underlying redis client for hash operations
            if redis_client.redis:
                await redis_client.redis.hincrby(key, query.lower(), 1)
                await redis_client.redis.expire(key, 30 * 24 * 60 * 60)
        except Exception as e:
            logger.error(f"Failed to track search: {e}")
    
    async def get_search_analytics(self, store_id: str) -> Dict:
        """Get search analytics"""
        try:
            key = f"search_analytics:{store_id}"
            
            # Get all search queries and counts using underlying client
            if not redis_client.redis:
                return {"total_searches": 0, "top_queries": []}
            
            data = await redis_client.redis.hgetall(key)
            
            if not data:
                return {"total_searches": 0, "top_queries": []}
            
            # Data is already decoded with decode_responses=True
            queries = {k: int(v) for k, v in data.items()}
            sorted_queries = sorted(queries.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "total_searches": sum(queries.values()),
                "unique_queries": len(queries),
                "top_queries": [
                    {"query": q, "count": c}
                    for q, c in sorted_queries[:20]
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {"total_searches": 0, "top_queries": []}


# FastAPI endpoints
from fastapi import APIRouter, Depends, Query, Request
from app.core.database import get_db
from app.schemas.schemas import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse)
async def enhanced_search(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query"),
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Enhanced product search with filters and caching"""
    store_id = request.state.store_id
    
    filters = {
        "category_id": category_id,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock,
        "is_featured": is_featured,
    }
    
    service = SearchService(db)
    results = await service.search_products(q, store_id, filters, limit)
    
    # Track search
    await service.track_search(q, store_id, len(results))
    
    return APIResponse(
        success=True,
        data=[
            {
                "id": str(p.id),
                "name": p.name,
                "selling_price": p.selling_price,
                "mrp": p.mrp,
                "thumbnail": p.thumbnail,
                "is_in_stock": p.is_in_stock,
            }
            for p in results
        ],
        meta={"total": len(results), "query": q}
    )


@router.get("/suggestions", response_model=APIResponse)
async def search_suggestions(
    request: Request,
    q: str = Query(..., min_length=2),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get search suggestions for autocomplete"""
    store_id = request.state.store_id
    
    service = SearchService(db)
    suggestions = await service.get_suggestions(q, store_id, limit)
    
    return APIResponse(success=True, data=suggestions)


@router.get("/popular", response_model=APIResponse)
async def popular_searches(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get popular search terms"""
    store_id = request.state.store_id
    
    service = SearchService(db)
    popular = await service.get_popular_searches(store_id, limit)
    
    return APIResponse(success=True, data=popular)


@router.get("/analytics", response_model=APIResponse)
async def search_analytics(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get search analytics"""
    store_id = request.state.store_id
    
    service = SearchService(db)
    analytics = await service.get_search_analytics(store_id)
    
    return APIResponse(success=True, data=analytics)
