"""
Order API Endpoints
Handle customer orders and order management
Like Amazon/Flipkart order management system
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User
from app.models.models import Order, OrderItem, Product, Store
from app.schemas.schemas import APIResponse, OrderResponse

router = APIRouter()


@router.get("/admin", response_model=APIResponse)
async def get_admin_orders(
    store_id: str = Query(..., description="Store ID for multi-tenant filtering"),
    status_filter: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders for store admin/owner (like Flipkart/Amazon admin panel)
    - Filter by status
    - Search by order number, customer info
    - Pagination
    """
    # Check if user is admin
    if current_user.role.value.upper() not in ['ADMIN', 'SUPER_ADMIN']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only store admins can access this endpoint"
        )
    
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Build query with joins for order items
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(Order.store_id == store_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Order.order_status == status_filter)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Order.order_number.ilike(search_pattern)) |
            (Order.customer_name.ilike(search_pattern)) |
            (Order.customer_email.ilike(search_pattern)) |
            (Order.customer_phone.ilike(search_pattern))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    orders = query.order_by(desc(Order.created_at))\
                  .offset((page - 1) * per_page)\
                  .limit(per_page)\
                  .all()

    # Format response
    orders_data = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "payment_method": order.payment_method,
            "subtotal": float(order.subtotal),
            "tax_amount": float(order.tax_amount),
            "delivery_charge": float(order.delivery_charge),
            "total_amount": float(order.total_amount),
            "items_count": len(order.items),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total": float(item.total)
                }
                for item in order.items
            ]
        }
        orders_data.append(order_dict)

    return APIResponse(
        success=True,
        data=orders_data,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    )


@router.get("/admin/stats", response_model=APIResponse)
async def get_order_stats(
    store_id: str = Query(..., description="Store ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order statistics for admin dashboard"""
    if current_user.role.value.upper() not in ['ADMIN', 'SUPER_ADMIN']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get order counts by status
    status_counts = db.query(
        Order.order_status,
        func.count(Order.id).label('count')
    ).filter(Order.store_id == store_id)\
     .group_by(Order.order_status)\
     .all()
    
    # Get total revenue
    total_revenue = db.query(
        func.sum(Order.total_amount)
    ).filter(
        Order.store_id == store_id,
        Order.payment_status.in_(['paid', 'cod'])  # COD or paid orders count as revenue
    ).scalar() or 0
    
    # Get today's orders
    today_orders = db.query(func.count(Order.id))\
        .filter(
            Order.store_id == store_id,
            func.date(Order.created_at) == datetime.now().date()
        ).scalar() or 0
    
    return APIResponse(
        success=True,
        data={
            "status_counts": {row[0]: row[1] for row in status_counts},
            "total_revenue": float(total_revenue),
            "today_orders": today_orders
        }
    )


@router.get("/customer", response_model=APIResponse)
async def get_customer_orders(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get orders for logged-in customer (like Amazon 'My Orders' page)
    Filter by customer email AND store_id for proper multi-tenant isolation
    """
    # Get store_id from request state (set by TenantMiddleware)
    store_id = request.state.store_id
    
    # Query orders by customer email AND store_id (multi-tenant isolation)
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.customer_email == current_user.email,
        Order.store_id == store_id
    )
    
    total = query.count()
    
    orders = query.order_by(desc(Order.created_at))\
                  .offset((page - 1) * per_page)\
                  .limit(per_page)\
                  .all()
    
    orders_data = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "payment_method": order.payment_method,
            "subtotal": float(order.subtotal),
            "tax_amount": float(order.tax_amount),
            "delivery_charge": float(order.delivery_charge),
            "total_amount": float(order.total_amount),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": [
                {
                    "id": item.id,
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
                "address": order.shipping_address,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "postal_code": order.shipping_postal_code
            }
        }
        orders_data.append(order_dict)
    
    return APIResponse(
        success=True,
        data=orders_data,
        meta={
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    )


@router.put("/admin/{order_id}/status", response_model=APIResponse)
async def update_order_status(
    order_id: str,
    order_status: str = Query(..., description="New order status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order status (admin only) - like Flipkart order processing"""
    if current_user.role.value.upper() not in ['ADMIN', 'SUPER_ADMIN']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Valid statuses
    valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    if order_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.order_status
    order.order_status = order_status
    order.updated_at = datetime.now()
    
    db.commit()
    db.refresh(order)
    
    return APIResponse(
        success=True,
        data={
            "order_id": order.id,
            "order_number": order.order_number,
            "old_status": old_status,
            "new_status": order.order_status,
            "updated_at": order.updated_at.isoformat()
        },
        message=f"Order status updated from {old_status} to {order_status}"
    )
