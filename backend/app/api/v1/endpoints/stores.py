"""
Store Management API Endpoints
For admin/store owner dashboard
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db, get_read_db
from app.schemas.schemas import StoreResponse, APIResponse
from app.models.models import Store, Product, Order, OrderStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=APIResponse)
async def list_stores(db: Session = Depends(get_read_db)):
    """Get all active stores"""
    stores = db.query(Store).filter(Store.is_active == True).all()
    
    stores_data = []
    for store in stores:
        stores_data.append({
            "id": str(store.id),
            "name": store.name,
            "slug": store.slug,
            "domain": store.domain,
            "city": store.city,
            "status": store.status,
            "logo_url": store.logo_url
        })
    
    return APIResponse(
        success=True,
        data=stores_data,
        meta={"total": len(stores_data)}
    )


@router.get("/dashboard/stats", response_model=APIResponse)
async def get_dashboard_stats(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_read_db)
):
    """
    Get dashboard statistics
    
    - Total orders, revenue
    - Product counts
    - Low stock alerts
    - Recent activity
    """
    store_id = UUID(request.state.store_id)
    
    # Date range
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Order statistics
    orders_query = db.query(Order).filter(
        and_(
            Order.store_id == store_id,
            Order.created_at >= start_date
        )
    )
    
    total_orders = orders_query.count()
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        and_(
            Order.store_id == store_id,
            Order.created_at >= start_date,
            Order.order_status != OrderStatus.CANCELLED
        )
    ).scalar() or 0
    
    pending_orders = orders_query.filter(
        Order.order_status == OrderStatus.PENDING
    ).count()
    
    # Product statistics
    total_products = db.query(func.count(Product.id)).filter(
        Product.store_id == store_id
    ).scalar() or 0
    
    active_products = db.query(func.count(Product.id)).filter(
        and_(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.is_in_stock == True
        )
    ).scalar() or 0
    
    low_stock_products = db.query(func.count(Product.id)).filter(
        and_(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.quantity <= Product.low_stock_threshold,
            Product.quantity > 0
        )
    ).scalar() or 0
    
    out_of_stock = db.query(func.count(Product.id)).filter(
        and_(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.quantity == 0
        )
    ).scalar() or 0
    
    return APIResponse(
        success=True,
        data={
            "period_days": days,
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "revenue": float(total_revenue)
            },
            "products": {
                "total": total_products,
                "active": active_products,
                "low_stock": low_stock_products,
                "out_of_stock": out_of_stock
            }
        }
    )


@router.get("/dashboard/low-stock", response_model=APIResponse)
async def get_low_stock_products(
    request: Request,
    limit: int = 50,
    db: Session = Depends(get_read_db)
):
    """Get products with low stock"""
    store_id = UUID(request.state.store_id)
    
    products = db.query(Product).filter(
        and_(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.quantity <= Product.low_stock_threshold
        )
    ).order_by(Product.quantity.asc()).limit(limit).all()
    
    return APIResponse(
        success=True,
        data=[
            {
                "id": str(p.id),
                "name": p.name,
                "sku": p.sku,
                "quantity": p.quantity,
                "low_stock_threshold": p.low_stock_threshold,
                "last_synced_at": p.last_synced_at.isoformat() if p.last_synced_at else None
            }
            for p in products
        ],
        meta={"total": len(products)}
    )


@router.get("/dashboard/recent-orders", response_model=APIResponse)
async def get_recent_orders(
    request: Request,
    limit: int = 20,
    status_filter: Optional[OrderStatus] = None,
    db: Session = Depends(get_read_db)
):
    """Get recent orders"""
    store_id = UUID(request.state.store_id)
    
    query = db.query(Order).filter(Order.store_id == store_id)
    
    if status_filter:
        query = query.filter(Order.order_status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    
    return APIResponse(
        success=True,
        data=[
            {
                "id": str(o.id),
                "order_number": o.order_number,
                "customer_name": o.customer_name,
                "customer_phone": o.customer_phone,
                "order_status": o.order_status,
                "payment_status": o.payment_status,
                "total_amount": o.total_amount,
                "created_at": o.created_at.isoformat(),
                "items_count": len(o.items)
            }
            for o in orders
        ],
        meta={"total": len(orders)}
    )
