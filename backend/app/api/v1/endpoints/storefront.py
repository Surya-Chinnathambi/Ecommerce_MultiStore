"""
Storefront API Endpoints
Public-facing endpoints for customers
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import random
import string

from app.core.database import get_read_db, get_db
from app.core.security import get_current_user, get_optional_user
from app.models.auth_models import User
from app.schemas.schemas import (
    ProductResponse, CategoryResponse, StoreResponse, APIResponse
)
from app.models.models import Product, Category, Store, Order, OrderItem, OrderStatus, PaymentStatus
from app.models.marketplace_models import PincodeDelivery, Coupon, CouponUsage, CouponType
from app.models.review_models import ProductReview
from app.core.redis import redis_client, CacheKeys
from app.core.config import settings
from app.services.order_service import get_order_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/store-info", response_model=APIResponse)
async def get_store_info(
    request: Request,
    db: Session = Depends(get_read_db)
):
    """
    Get store information for storefront
    
    - Cached for performance
    - Includes branding, contact info
    - No authentication required
    """
    store_id = request.state.store_id
    
    # Try cache
    cache_key = CacheKeys.store_config(store_id)
    cached = await redis_client.get_json(cache_key)
    
    if cached:
        return APIResponse(success=True, data=cached)
    
    # Query database
    store = db.query(Store).filter(Store.id == store_id).first()
    
    if not store or not store.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    store_data = {
        "id": str(store.id),
        "name": store.name,
        "domain": store.domain,
        "logo_url": store.logo_url,
        "primary_color": store.primary_color,
        "secondary_color": store.secondary_color,
        "address": store.address,
        "city": store.city,
        "state": store.state,
        "pincode": store.pincode,
        "owner_phone": store.owner_phone,
        "currency": store.currency,
        "language": store.language
    }
    
    # Cache for 1 hour
    await redis_client.set_json(
        cache_key,
        store_data,
        ttl=settings.CACHE_TTL_STORE_CONFIG
    )
    
    return APIResponse(success=True, data=store_data)


@router.get("/categories", response_model=APIResponse)
async def list_categories(
    request: Request,
    db: Session = Depends(get_read_db)
):
    """
    List all active categories
    
    - Hierarchical structure
    - Cached
    """
    store_id = request.state.store_id
    
    # Try cache
    cache_key = CacheKeys.categories(store_id)
    cached = await redis_client.get_json(cache_key)
    
    if cached:
        return APIResponse(success=True, data=cached)
    
    # Query database
    categories = db.query(Category).filter(
        and_(
            Category.store_id == store_id,
            Category.is_active == True
        )
    ).order_by(Category.display_order.asc(), Category.name.asc()).all()
    
    categories_data = [CategoryResponse.model_validate(c).model_dump(mode='json') for c in categories]
    
    # Cache for 30 minutes
    await redis_client.set_json(
        cache_key,
        categories_data,
        ttl=settings.CACHE_TTL_CATEGORIES
    )
    
    return APIResponse(
        success=True,
        data=categories_data,
        meta={"total": len(categories_data)}
    )


@router.get("/products", response_model=APIResponse)
async def list_storefront_products(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|price|newest|rating)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_read_db)
):
    """
    List products for storefront
    
    - Only shows active, in-stock products
    - Customer-friendly sorting with direction
    - Supports sort_by: name, price, newest, rating
    """
    store_id = request.state.store_id
    
    # For rating sort we need to join with reviews
    if sort_by == "rating":
        query = db.query(
            Product,
            func.coalesce(func.avg(ProductReview.rating), 0).label("avg_rating")
        ).outerjoin(
            ProductReview, ProductReview.product_id == Product.id
        ).filter(
            and_(
                Product.store_id == store_id,
                Product.is_active == True,
                Product.is_in_stock == True
            )
        ).group_by(Product.id)
    else:
        query = db.query(Product).filter(
            and_(
                Product.store_id == store_id,
                Product.is_active == True,
                Product.is_in_stock == True
            )
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Apply sorting
    if sort_by == "price":
        query = query.order_by(Product.selling_price.asc() if order == "asc" else Product.selling_price.desc())
    elif sort_by == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort_by == "rating":
        avg_col = func.coalesce(func.avg(ProductReview.rating), 0)
        query = query.order_by(avg_col.asc() if order == "asc" else avg_col.desc())
    else:  # name
        query = query.order_by(Product.name.asc() if order == "asc" else Product.name.desc())
    
    total = query.count()
    offset = (page - 1) * per_page
    rows = query.offset(offset).limit(per_page).all()
    
    # rows may be (Product, avg_rating) tuples when sort_by==rating
    products_out = []
    for row in rows:
        p = row[0] if isinstance(row, tuple) else row
        avg_rating = float(row[1]) if isinstance(row, tuple) else None
        product_dict = {
            "id": str(p.id),
            "name": p.name,
            "slug": p.slug,
            "short_description": p.short_description,
            "mrp": p.mrp,
            "selling_price": p.selling_price,
            "discount_percent": p.discount_percent,
            "thumbnail": p.thumbnail,
            "images": p.images,
            "category_id": str(p.category_id) if p.category_id else None,
            "is_featured": p.is_featured,
            "unit": p.unit,
            "quantity": p.quantity,
            "is_in_stock": p.is_in_stock,
        }
        if avg_rating is not None:
            product_dict["average_rating"] = round(avg_rating, 2)
        products_out.append(product_dict)

    total_pages = (total + per_page - 1) // per_page

    return APIResponse(
        success=True,
        data={
            "products": products_out,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    )


@router.get("/products/{product_id}", response_model=APIResponse)
async def get_storefront_product(
    request: Request,
    product_id: UUID,
    db: Session = Depends(get_read_db)
):
    """Get product details for storefront"""
    store_id = request.state.store_id
    
    # Try cache
    cache_key = CacheKeys.product(store_id, str(product_id))
    cached = await redis_client.get_json(cache_key)
    
    if cached:
        return APIResponse(success=True, data=cached)
    
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
    
    product_data = {
        "id": str(product.id),
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "short_description": product.short_description,
        "mrp": product.mrp,
        "selling_price": product.selling_price,
        "discount_percent": product.discount_percent,
        "quantity": product.quantity,
        "is_in_stock": product.is_in_stock,
        "unit": product.unit,
        "sku": product.sku,
        "images": product.images,
        "thumbnail": product.thumbnail,
        "attributes": product.attributes
    }
    
    # Cache for 15 minutes
    await redis_client.set_json(
        cache_key,
        product_data,
        ttl=settings.CACHE_TTL_PRODUCTS
    )
    
    return APIResponse(success=True, data=product_data)


@router.get("/featured-products", response_model=APIResponse)
async def get_featured_products(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_read_db)
):
    """Get featured products for homepage"""
    store_id = request.state.store_id
    
    products = db.query(Product).filter(
        and_(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.is_featured == True,
            Product.is_in_stock == True
        )
    ).order_by(Product.selling_price.desc()).limit(limit).all()
    
    return APIResponse(
        success=True,
        data=[
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "selling_price": p.selling_price,
                "mrp": p.mrp,
                "discount_percent": p.discount_percent,
                "thumbnail": p.thumbnail,
                "quantity": p.quantity,
                "is_in_stock": p.is_in_stock
            }
            for p in products
        ],
        meta={"total": len(products)}
    )


@router.post("/orders", response_model=APIResponse)
async def create_order(
    request: Request,
    order_data: Dict[str, Any] = Body(...),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order from checkout
    """
    store_id = request.state.store_id
    service = get_order_service(db)
    try:
        order = await service.create_order(
            store_id=store_id,
            user_id=current_user.id if current_user else None,
            order_data=order_data
        )
        db.commit()
        db.refresh(order)
        
        # Async notification
        try:
            from app.services.websocket_manager import notify_new_order
            await notify_new_order(
                store_id=str(store_id),
                order_id=str(order.id),
                order_number=order.order_number,
                total_amount=float(order.total_amount),
                customer_name=order.customer_name or ""
            )
        except Exception:
            pass

        return APIResponse(
            success=True,
            data={
                "order_number": order.order_number,
                "order_id": str(order.id),
                "subtotal": float(order.subtotal),
                "total": float(order.total_amount),
                "status": order.order_status.value if hasattr(order.order_status, "value") else order.order_status,
                "created_at": order.created_at.isoformat()
            },
            message="Order placed successfully"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to place order")


@router.get("/orders/{order_number}", response_model=APIResponse)
async def get_order_details(
    request: Request,
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_read_db)
):
    """Get order details by order number"""
    store_id = request.state.store_id
    
    order = db.query(Order).filter(
        Order.store_id == store_id,
        Order.order_number == order_number
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Ownership check
    is_owner = (order.user_id == current_user.id) or (order.customer_email == current_user.email)
    if not is_owner:
        # Check if admin/superadmin (they can view any order)
        from app.models.auth_models import UserRole
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
    
    # Get order items
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    
    return APIResponse(
        success=True,
        data={
            "order_number": order.order_number,
            "status": order.order_status.value,
            "payment_status": order.payment_status.value,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "delivery_city": order.delivery_city,
            "delivery_state": order.delivery_state,
            "delivery_pincode": order.delivery_pincode,
            "subtotal": order.subtotal,
            "tax": order.tax_amount,
            "shipping_cost": order.delivery_charge,
            "total": order.total_amount,
            "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "price": item.price,
                    "subtotal": item.subtotal
                }
                for item in items
            ]
        }
    )


@router.get("/orders/{order_number}/track", response_model=APIResponse)
async def track_order(
    request: Request,
    order_number: str,
    email: Optional[str] = Query(None, description="Verify email for guest tracking"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_read_db)
):
    """
    Track order status
    - Returns full details if authenticated owner
    - Returns basic status if guest provides matching email
    """
    store_id = request.state.store_id
    
    order = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.store_id == store_id,
        Order.order_number == order_number
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Permission check
    is_authorized = False
    if current_user:
        from app.models.auth_models import UserRole
        if order.user_id == current_user.id or order.customer_email == current_user.email:
            is_authorized = True
        elif current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            is_authorized = True
    
    if not is_authorized and email:
        if order.customer_email.lower() == email.lower():
            is_authorized = True

    if not is_authorized:
        # If not authorized, ONLY return status, hide PII
        return APIResponse(
            success=True,
            data={
                "order_number": order.order_number,
                "order_status": order.order_status.value if hasattr(order.order_status, "value") else order.order_status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "message": "Full details hidden. Provide email or login to see more."
            }
        )

    # Return full order details
    return APIResponse(
        success=True,
        data={
            "id": order.id,
            "order_number": order.order_number,
            "order_status": order.order_status.value,
            "payment_status": order.payment_status.value,
            "payment_method": order.payment_method,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "delivery_city": order.delivery_city,
            "delivery_state": order.delivery_state,
            "delivery_pincode": order.delivery_pincode,
            "delivery_landmark": order.delivery_landmark,
            "notes": order.notes,
            "subtotal": float(order.subtotal),
            "tax_amount": float(order.tax_amount),
            "delivery_charge": float(order.delivery_charge),
            "total_amount": float(order.total_amount),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total": float(item.total),
                    "product": {
                        "id": item.product.id if item.product else None,
                        "image_url": (item.product.images[0] if item.product and getattr(item.product, "images", None) else None)
                    } if item.product else None
                }
                for item in order.items
            ],
            "shipping_address": {
                "address": order.delivery_address,
                "city": order.delivery_city,
                "state": order.delivery_state,
                "postal_code": order.delivery_pincode
            }
        }
    )


# ──────────────────────────────────────────────────────────────────────────────
# PINCODE DELIVERY ESTIMATOR
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/pincode/{pincode}", summary="Check delivery availability for a pincode")
def check_pincode_delivery(
    pincode: str,
    request: Request,
    db: Session = Depends(get_read_db),
):
    """Return delivery ETA and serviceability for a given pincode."""
    store_id = request.state.store_id

    record = (
        db.query(PincodeDelivery)
        .filter(
            PincodeDelivery.store_id == store_id,
            PincodeDelivery.pincode == pincode,
        )
        .first()
    )

    if record and not record.is_serviceable:
        raise HTTPException(
            status_code=400,
            detail={"serviceable": False, "message": "Delivery not available to this pincode."},
        )

    if record:
        return {
            "success": True,
            "data": {
                "pincode": pincode,
                "serviceable": True,
                "standard_days": record.standard_days,
                "express_days": record.express_days,
                "same_day": record.same_day,
                "cod_available": record.cod_available,
                "state": record.state,
                "city": record.city,
            },
        }

    # Pincode not in database — return best-effort generic estimate
    return {
        "success": True,
        "data": {
            "pincode": pincode,
            "serviceable": True,
            "standard_days": 5,
            "express_days": None,
            "same_day": False,
            "cod_available": True,
            "state": None,
            "city": None,
        },
    }


