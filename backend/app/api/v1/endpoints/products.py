"""
Product API Endpoints
CRUD operations for products
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
from uuid import UUID
import logging

from app.core.database import get_db, get_read_db
from app.schemas.schemas import (
    ProductResponse, ProductListResponse, ProductCreate,
    ProductUpdate, APIResponse
)
from app.models.models import Product, Store
from app.core.redis import redis_client, CacheKeys
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=APIResponse)
async def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    sort_by: str = Query("created_at", pattern="^(name|selling_price|created_at|updated_at|rating|popularity)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_read_db)
):
    """
    List products with filtering, search, and pagination
    
    - Cached for performance
    - Supports full-text search
    - Multiple filters including rating
    - Sorting options including popularity
    """
    from app.models.review_models import ProductReview
    
    store_id = request.state.store_id
    
    # Build base query with left join for reviews
    query = db.query(
        Product,
        func.coalesce(func.avg(ProductReview.rating), 0).label('avg_rating'),
        func.count(ProductReview.id).label('review_count')
    ).outerjoin(ProductReview).filter(
        and_(
            Product.store_id == store_id,
            Product.is_active == True
        )
    ).group_by(Product.id)
    
    # Apply filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        # Enhanced search across multiple fields
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.barcode.ilike(search_term)
            )
        )
    
    if in_stock is not None:
        query = query.filter(Product.is_in_stock == in_stock)
    
    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)
    
    if min_price is not None:
        query = query.filter(Product.selling_price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.selling_price <= max_price)
    
    if min_rating is not None:
        query = query.having(func.avg(ProductReview.rating) >= min_rating)
    
    # Get total count before sorting
    total = query.count()
    
    # Apply sorting
    if sort_by == "rating":
        if order == "asc":
            query = query.order_by(func.avg(ProductReview.rating).asc())
        else:
            query = query.order_by(func.avg(ProductReview.rating).desc())
    elif sort_by == "popularity":
        # Sort by number of reviews or sales
        if order == "asc":
            query = query.order_by(func.count(ProductReview.id).asc())
        else:
            query = query.order_by(func.count(ProductReview.id).desc())
    else:
        if order == "asc":
            query = query.order_by(getattr(Product, sort_by).asc())
        else:
            query = query.order_by(getattr(Product, sort_by).desc())
    
    # Apply pagination
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()
    
    # Format products with ratings
    products_data = []
    for product, avg_rating, review_count in results:
        product_dict = ProductResponse.from_orm(product).dict()
        product_dict['average_rating'] = round(float(avg_rating), 2) if avg_rating else 0.0
        product_dict['review_count'] = review_count
        products_data.append(product_dict)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return APIResponse(
        success=True,
        data={
            "products": products_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    )


@router.get("/{product_id}", response_model=APIResponse)
async def get_product(
    request: Request,
    product_id: UUID,
    db: Session = Depends(get_read_db)
):
    """Get single product by ID with caching"""
    store_id = request.state.store_id
    
    # Try cache first
    cache_key = CacheKeys.product(store_id, str(product_id))
    cached = await redis_client.get_json(cache_key)
    
    if cached:
        return APIResponse(success=True, data=cached)
    
    # Query database
    product = db.query(Product).filter(
        and_(
            Product.id == product_id,
            Product.store_id == store_id,
            Product.is_active == True
        )
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Cache result
    product_data = ProductResponse.from_orm(product).dict()
    await redis_client.set_json(
        cache_key,
        product_data,
        ttl=settings.CACHE_TTL_PRODUCTS
    )
    
    return APIResponse(success=True, data=product_data)


@router.get("/{product_id}/inventory", response_model=APIResponse)
async def get_product_inventory(
    request: Request,
    product_id: UUID,
    db: Session = Depends(get_read_db)
):
    """
    Get real-time inventory for a product
    
    - Shorter cache TTL (1 minute)
    - Critical for checkout validation
    """
    store_id = request.state.store_id
    
    # Cache key for inventory
    cache_key = CacheKeys.inventory(store_id, str(product_id))
    cached = await redis_client.get_json(cache_key)
    
    if cached:
        return APIResponse(success=True, data=cached)
    
    # Query database
    product = db.query(Product).filter(
        and_(
            Product.id == product_id,
            Product.store_id == store_id
        )
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    inventory_data = {
        "product_id": str(product.id),
        "quantity": product.quantity,
        "is_in_stock": product.is_in_stock,
        "low_stock": product.quantity <= product.low_stock_threshold,
        "last_updated": product.updated_at.isoformat() if product.updated_at else None
    }
    
    # Cache with short TTL
    await redis_client.set_json(
        cache_key,
        inventory_data,
        ttl=settings.CACHE_TTL_INVENTORY
    )
    
    return APIResponse(success=True, data=inventory_data)


@router.get("/categories/{category_id}", response_model=APIResponse)
async def list_products_by_category(
    request: Request,
    category_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_read_db)
):
    """List all products in a category"""
    store_id = request.state.store_id
    
    query = db.query(Product).filter(
        and_(
            Product.store_id == store_id,
            Product.category_id == category_id,
            Product.is_active == True,
            Product.is_in_stock == True
        )
    ).order_by(Product.name.asc())
    
    total = query.count()
    offset = (page - 1) * per_page
    products = query.offset(offset).limit(per_page).all()
    
    return APIResponse(
        success=True,
        data={
            "products": [ProductResponse.from_orm(p).dict() for p in products],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    )
