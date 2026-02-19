"""
Product API Endpoints
CRUD operations for products
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
from uuid import UUID
import logging
import uuid as _uuid
import re

from app.core.database import get_db, get_read_db
from app.core.security import get_current_user
from app.schemas.schemas import (
    ProductResponse, ProductListResponse, ProductCreate,
    ProductUpdate, APIResponse
)
from app.models.models import Product, Store, Category
from app.models.auth_models import User
from app.core.redis import redis_client, CacheKeys
from app.core.config import settings
from app.services.cache_service import cache_service

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
    include_inactive: bool = Query(False, description="Include inactive products (admin use)"),
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

    # ── Cache lookup ──────────────────────────────────────────────────────────
    _cache_params = {
        "page": page, "per_page": per_page,
        "category_id": str(category_id) if category_id else None,
        "search": search, "in_stock": in_stock,
        "is_featured": is_featured, "min_price": min_price,
        "max_price": max_price, "min_rating": min_rating,
        "sort_by": sort_by, "order": order,
    }
    _cache_key = CacheKeys.product_list(store_id, **_cache_params)
    # Skip cache when requesting inactive products (admin)
    if not include_inactive:
        _cached = await cache_service.get_product_list(store_id, **_cache_params)
        if _cached is not None:
            return APIResponse(success=True, data=_cached)

    # Build base query
    _active_filters = [Product.store_id == store_id]
    if not include_inactive:
        _active_filters.append(Product.is_active == True)

    # Build base query with left join for reviews
    query = db.query(
        Product,
        func.coalesce(func.avg(ProductReview.rating), 0).label('avg_rating'),
        func.count(ProductReview.id).label('review_count')
    ).outerjoin(ProductReview).filter(
        and_(*_active_filters)
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

    result_data = {
        "products": products_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }

    # ── Populate cache (only for public, active-only queries) ─────────────────
    if not include_inactive:
        await cache_service.set_product_list(store_id, result_data, **_cache_params)

    return APIResponse(success=True, data=result_data)


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
    
    # Query database — eager-load category to avoid N+1 on serialisation
    from sqlalchemy.orm import joinedload
    product = db.query(Product).options(
        joinedload(Product.category)
    ).filter(
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


# ─── Admin Write Endpoints ────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convert product name to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request,
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new product (admin only)."""
    if current_user.role.value.upper() not in ('ADMIN', 'SUPER_ADMIN'):
        raise HTTPException(status_code=403, detail="Admin access required")

    store_id = request.state.store_id

    # Store admin can only create products in their own store
    if current_user.role.value.upper() != 'SUPER_ADMIN':
        if not current_user.store_id or str(current_user.store_id) != str(store_id):
            raise HTTPException(status_code=403, detail="You can only manage your own store's products")

    # Check duplicate external_id
    existing = db.query(Product).filter(
        Product.store_id == store_id,
        Product.external_id == product_data.external_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with external_id '{product_data.external_id}' already exists")

    # Ensure slug is unique; auto-suffix if needed
    slug = product_data.slug or _slugify(product_data.name)
    base_slug = slug
    attempt = 1
    while db.query(Product).filter(Product.store_id == store_id, Product.slug == slug).first():
        slug = f"{base_slug}-{attempt}"
        attempt += 1

    # Validate category belongs to this store
    if product_data.category_id:
        cat = db.query(Category).filter(
            Category.id == product_data.category_id,
            Category.store_id == store_id
        ).first()
        if not cat:
            raise HTTPException(status_code=400, detail="Category not found in this store")

    discount_pct = round((1 - product_data.selling_price / product_data.mrp) * 100, 2) if product_data.mrp else 0

    product = Product(
        id=_uuid.uuid4(),
        store_id=store_id,
        external_id=product_data.external_id,
        name=product_data.name,
        slug=slug,
        description=product_data.description,
        short_description=product_data.short_description,
        mrp=product_data.mrp,
        selling_price=product_data.selling_price,
        discount_percent=discount_pct,
        quantity=product_data.quantity,
        unit=product_data.unit,
        sku=product_data.sku,
        barcode=product_data.barcode,
        category_id=product_data.category_id,
        is_active=True,
        is_in_stock=product_data.quantity > 0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    await cache_service.invalidate_store_products(store_id)
    logger.info(f"Product created: {product.id} in store {store_id} by {current_user.id}")

    return APIResponse(
        success=True,
        data=ProductResponse.from_orm(product).dict(),
        message="Product created successfully"
    )


@router.patch("/{product_id}", response_model=APIResponse)
async def update_product(
    request: Request,
    product_id: UUID,
    updates: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update product fields (admin only). Only provided fields are changed."""
    if current_user.role.value.upper() not in ('ADMIN', 'SUPER_ADMIN'):
        raise HTTPException(status_code=403, detail="Admin access required")

    store_id = request.state.store_id

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == store_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Store admin ownership check
    if current_user.role.value.upper() != 'SUPER_ADMIN':
        if not current_user.store_id or str(current_user.store_id) != str(store_id):
            raise HTTPException(status_code=403, detail="You can only manage your own store's products")

    # Apply only provided fields
    update_data = updates.dict(exclude_unset=True)

    if "category_id" in update_data and update_data["category_id"]:
        cat = db.query(Category).filter(
            Category.id == update_data["category_id"],
            Category.store_id == store_id
        ).first()
        if not cat:
            raise HTTPException(status_code=400, detail="Category not found in this store")

    for field, value in update_data.items():
        setattr(product, field, value)

    # Recalculate derived fields
    if "selling_price" in update_data or "mrp" in update_data:
        if product.mrp and product.mrp > 0:
            product.discount_percent = round((1 - product.selling_price / product.mrp) * 100, 2)

    if "quantity" in update_data:
        product.is_in_stock = (product.quantity or 0) > 0

    from datetime import datetime
    product.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(product)

    # Invalidate caches
    await cache_service.invalidate_store_products(store_id)
    cache_key = CacheKeys.product(store_id, str(product_id))
    await redis_client.delete(cache_key)

    logger.info(f"Product {product_id} updated by {current_user.id}")

    return APIResponse(
        success=True,
        data=ProductResponse.from_orm(product).dict(),
        message="Product updated successfully"
    )


@router.delete("/{product_id}", response_model=APIResponse)
async def delete_product(
    request: Request,
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete a product by marking it inactive (admin only)."""
    if current_user.role.value.upper() not in ('ADMIN', 'SUPER_ADMIN'):
        raise HTTPException(status_code=403, detail="Admin access required")

    store_id = request.state.store_id

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == store_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if current_user.role.value.upper() != 'SUPER_ADMIN':
        if not current_user.store_id or str(current_user.store_id) != str(store_id):
            raise HTTPException(status_code=403, detail="You can only manage your own store's products")

    from datetime import datetime
    product.is_active = False
    product.updated_at = datetime.utcnow()
    db.commit()

    await cache_service.invalidate_store_products(store_id)
    cache_key = CacheKeys.product(store_id, str(product_id))
    await redis_client.delete(cache_key)

    logger.info(f"Product {product_id} deactivated by {current_user.id}")

    return APIResponse(
        success=True,
        data={"product_id": str(product_id), "is_active": False},
        message="Product deactivated successfully"
    )


@router.post("/bulk-status", response_model=APIResponse)
async def bulk_update_product_status(
    request: Request,
    payload: dict = Body(..., example={"product_ids": ["uuid1", "uuid2"], "is_active": False}),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk activate / deactivate products (admin only)."""
    if current_user.role.value.upper() not in ('ADMIN', 'SUPER_ADMIN'):
        raise HTTPException(status_code=403, detail="Admin access required")

    store_id = request.state.store_id
    product_ids = payload.get("product_ids", [])
    is_active = payload.get("is_active")

    if not product_ids:
        raise HTTPException(status_code=422, detail="product_ids list is required")
    if is_active is None:
        raise HTTPException(status_code=422, detail="is_active (bool) is required")

    from datetime import datetime
    updated = db.query(Product).filter(
        Product.id.in_(product_ids),
        Product.store_id == store_id
    ).update(
        {"is_active": is_active, "updated_at": datetime.utcnow()},
        synchronize_session="fetch"
    )
    db.commit()

    await cache_service.invalidate_store_products(store_id)
    logger.info(f"Bulk status update: {updated} products set is_active={is_active} by {current_user.id}")

    return APIResponse(
        success=True,
        data={"updated_count": updated, "is_active": is_active},
        message=f"{updated} products {'activated' if is_active else 'deactivated'}"
    )
