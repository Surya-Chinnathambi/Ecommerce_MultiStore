"""
Storefront API Endpoints
Public-facing endpoints for customers
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import random
import string

from app.core.database import get_read_db, get_db
from app.core.security import get_current_user
from app.models.auth_models import User
from app.schemas.schemas import (
    ProductResponse, CategoryResponse, StoreResponse, APIResponse
)
from app.models.models import Product, Category, Store, Order, OrderItem, OrderStatus, PaymentStatus
from app.core.redis import redis_client, CacheKeys
from app.core.config import settings

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
    
    categories_data = [CategoryResponse.from_orm(c).dict() for c in categories]
    
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
    sort_by: str = Query("name", pattern="^(name|price|newest)$"),
    db: Session = Depends(get_read_db)
):
    """
    List products for storefront
    
    - Only shows active, in-stock products
    - Customer-friendly sorting
    """
    store_id = request.state.store_id
    
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
        query = query.order_by(Product.selling_price.asc())
    elif sort_by == "newest":
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())
    
    total = query.count()
    offset = (page - 1) * per_page
    products = query.offset(offset).limit(per_page).all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return APIResponse(
        success=True,
        data={
            "products": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "slug": p.slug,
                    "short_description": p.short_description,
                    "mrp": p.mrp,
                    "selling_price": p.selling_price,
                    "discount_percent": p.discount_percent,
                    "thumbnail": p.thumbnail,
                    "images": p.images,
                    "is_featured": p.is_featured,
                    "unit": p.unit,
                    "quantity": p.quantity,
                    "is_in_stock": p.is_in_stock
                }
                for p in products
            ],
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order from checkout
    
    Expected order_data:
    {
        "customer_name": str,
        "customer_phone": str,
        "customer_email": str (optional),
        "delivery_address": str,
        "delivery_city": str,
        "delivery_state": str,
        "delivery_pincode": str,
        "delivery_landmark": str (optional),
        "notes": str (optional),
        "payment_method": str (COD/ONLINE),
        "items": [{"product_id": str, "quantity": int, "price": float}]
    }
    """
    store_id = request.state.store_id
    
    # Validate store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store or not store.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Extract order items
    items_data = order_data.get('items', [])
    if not items_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item"
        )
    
    # Fetch products and calculate totals
    subtotal = 0
    items_with_prices = []
    
    for item_data in items_data:
        product = db.query(Product).filter(
            Product.id == item_data['product_id'],
            Product.store_id == store_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data['product_id']} not found"
            )
        
        # Check stock
        if product.quantity < item_data['quantity']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.name}"
            )
        
        item_price = product.selling_price
        item_subtotal = item_price * item_data['quantity']
        subtotal += item_subtotal
        
        items_with_prices.append({
            'product': product,
            'quantity': item_data['quantity'],
            'price': item_price,
            'subtotal': item_subtotal
        })
    
    # Calculate totals
    tax = subtotal * 0.18  # 18% GST
    shipping_cost = 0.0 if subtotal > 500 else 50.0  # Free shipping above ₹500
    total = subtotal + tax + shipping_cost
    
    # Generate order number
    order_number = f"ORD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    
    # Create order
    order = Order(
        store_id=store_id,
        order_number=order_number,
        customer_name=order_data.get('customer_name'),
        customer_email=order_data.get('customer_email'),
        customer_phone=order_data.get('customer_phone'),
        delivery_address=order_data.get('delivery_address'),
        delivery_city=order_data.get('delivery_city'),
        delivery_state=order_data.get('delivery_state'),
        delivery_pincode=order_data.get('delivery_pincode'),
        delivery_landmark=order_data.get('delivery_landmark'),
        notes=order_data.get('notes'),
        payment_method=order_data.get('payment_method', 'COD'),
        subtotal=subtotal,
        tax_amount=tax,
        delivery_charge=shipping_cost,
        total_amount=total,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING
    )
    
    db.add(order)
    db.flush()  # Get order ID
    
    # Create order items and update inventory
    for item_info in items_with_prices:
        product = item_info['product']
        
        item_total = item_info['subtotal']
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=item_info['quantity'],
            unit_price=item_info['price'],
            subtotal=item_info['subtotal'],
            total=item_total
        )
        db.add(order_item)
        
        # Update product quantity
        product.quantity -= item_info['quantity']
        if product.quantity == 0:
            product.is_in_stock = False
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"Order {order_number} created for store {store_id}")
    
    return APIResponse(
        success=True,
        data={
            "order_number": order_number,
            "order_id": str(order.id),
            "total": total,
            "status": order.order_status.value,
            "created_at": order.created_at.isoformat()
        },
        meta={"message": "Order placed successfully"}
    )


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
    db: Session = Depends(get_read_db)
):
    """Track order status - returns full order details for payment and tracking"""
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
                        "image_url": item.product.image_url if item.product else None
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


