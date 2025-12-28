"""
Analytics API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, date

from app.core.database import get_db
from app.models.analytics_models import DailyAnalytics, ProductAnalytics, InventoryAlert
from app.models.models import Order, OrderItem, Product, Store
from app.models.auth_models import User
from app.models.review_models import ProductReview
from app.schemas.review_analytics_schemas import (
    DailyAnalyticsResponse, ProductAnalyticsResponse,
    DashboardStats, SalesChartData,
    InventoryAlertResponse, InventoryAlertCreate
)
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant import get_current_store_id

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics"""
    
    # Verify user is admin
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access dashboard"
        )
    
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Today's orders
    today_orders = db.query(Order).filter(
        Order.store_id == store_id,
        func.date(Order.created_at) == today
    ).all()
    
    today_orders_count = len(today_orders)
    today_revenue = sum(o.total_amount for o in today_orders)
    today_customers = len(set(o.user_id for o in today_orders if o.user_id))
    
    # Yesterday's orders for comparison
    yesterday_orders = db.query(Order).filter(
        Order.store_id == store_id,
        func.date(Order.created_at) == yesterday
    ).all()
    
    yesterday_orders_count = len(yesterday_orders)
    yesterday_revenue = sum(o.total_amount for o in yesterday_orders)
    yesterday_customers = len(set(o.user_id for o in yesterday_orders if o.user_id))
    
    # Calculate changes
    orders_change = ((today_orders_count - yesterday_orders_count) / yesterday_orders_count * 100) if yesterday_orders_count > 0 else 0
    revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
    customers_change = ((today_customers - yesterday_customers) / yesterday_customers * 100) if yesterday_customers > 0 else 0
    
    # Week metrics
    week_orders = db.query(Order).filter(
        Order.store_id == store_id,
        func.date(Order.created_at) >= week_ago
    ).all()
    
    week_orders_count = len(week_orders)
    week_revenue = sum(o.total_amount for o in week_orders)
    week_customers = len(set(o.user_id for o in week_orders if o.user_id))
    
    # Month metrics
    month_orders = db.query(Order).filter(
        Order.store_id == store_id,
        func.date(Order.created_at) >= month_ago
    ).all()
    
    month_orders_count = len(month_orders)
    month_revenue = sum(o.total_amount for o in month_orders)
    month_customers = len(set(o.user_id for o in month_orders if o.user_id))
    
    # Top products (last 30 days)
    top_products_data = db.query(
        Product.id,
        Product.name,
        Product.sku,
        Product.price,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.store_id == store_id,
        func.date(Order.created_at) >= month_ago
    ).group_by(Product.id).order_by(desc('total_sold')).limit(5).all()
    
    top_products = [
        {
            "id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "price": p.price,
            "units_sold": p.total_sold,
            "revenue": p.total_revenue
        }
        for p in top_products_data
    ]
    
    # Recent orders
    recent_orders_data = db.query(Order).filter(
        Order.store_id == store_id
    ).order_by(Order.created_at.desc()).limit(10).all()
    
    recent_orders = [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "customer_name": o.customer_name,
            "total_amount": o.total_amount,
            "status": o.status,
            "created_at": o.created_at.isoformat()
        }
        for o in recent_orders_data
    ]
    
    # Inventory alerts
    low_stock_count = db.query(Product).filter(
        Product.store_id == store_id,
        Product.quantity > 0,
        Product.quantity < 10,
        Product.is_active == True
    ).count()
    
    out_of_stock_count = db.query(Product).filter(
        Product.store_id == store_id,
        Product.quantity == 0,
        Product.is_active == True
    ).count()
    
    return DashboardStats(
        today_orders=today_orders_count,
        today_revenue=round(today_revenue, 2),
        today_customers=today_customers,
        orders_change=round(orders_change, 2),
        revenue_change=round(revenue_change, 2),
        customers_change=round(customers_change, 2),
        week_orders=week_orders_count,
        week_revenue=round(week_revenue, 2),
        week_customers=week_customers,
        month_orders=month_orders_count,
        month_revenue=round(month_revenue, 2),
        month_customers=month_customers,
        top_products=top_products,
        recent_orders=recent_orders,
        low_stock_products=low_stock_count,
        out_of_stock_products=out_of_stock_count
    )


@router.get("/sales-chart", response_model=SalesChartData)
async def get_sales_chart_data(
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get sales chart data for specified number of days"""
    
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access analytics"
        )
    
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Get daily analytics
    analytics = db.query(DailyAnalytics).filter(
        DailyAnalytics.store_id == store_id,
        DailyAnalytics.date >= start_date,
        DailyAnalytics.date <= end_date
    ).order_by(DailyAnalytics.date).all()
    
    # If no analytics, calculate on the fly
    if not analytics:
        dates = []
        revenue = []
        orders = []
        customers = []
        
        current_date = start_date
        while current_date <= end_date:
            day_orders = db.query(Order).filter(
                Order.store_id == store_id,
                func.date(Order.created_at) == current_date
            ).all()
            
            dates.append(current_date.strftime("%Y-%m-%d"))
            orders.append(len(day_orders))
            revenue.append(round(sum(o.total_amount for o in day_orders), 2))
            customers.append(len(set(o.user_id for o in day_orders if o.user_id)))
            
            current_date += timedelta(days=1)
    else:
        dates = [a.date.strftime("%Y-%m-%d") for a in analytics]
        revenue = [round(a.total_revenue, 2) for a in analytics]
        orders = [a.total_orders for a in analytics]
        customers = [a.total_customers for a in analytics]
    
    return SalesChartData(
        dates=dates,
        revenue=revenue,
        orders=orders,
        customers=customers
    )


@router.get("/inventory-alerts", response_model=List[InventoryAlertResponse])
async def get_inventory_alerts(
    resolved: Optional[bool] = Query(None),
    alert_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get inventory alerts"""
    
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access alerts"
        )
    
    query = db.query(InventoryAlert).filter(
        InventoryAlert.store_id == store_id
    )
    
    if resolved is not None:
        query = query.filter(InventoryAlert.is_resolved == resolved)
    
    if alert_type:
        query = query.filter(InventoryAlert.alert_type == alert_type)
    
    alerts = query.order_by(InventoryAlert.created_at.desc()).all()
    
    # Attach product details
    result = []
    for alert in alerts:
        alert_dict = InventoryAlertResponse.from_orm(alert)
        product = db.query(Product).filter(Product.id == alert.product_id).first()
        if product:
            alert_dict.product_name = product.name
            alert_dict.product_sku = product.sku
        result.append(alert_dict)
    
    return result


@router.post("/inventory-alerts", response_model=InventoryAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_alert(
    alert_data: InventoryAlertCreate,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Create an inventory alert (typically called by system)"""
    
    # Check if alert already exists and is unresolved
    existing = db.query(InventoryAlert).filter(
        InventoryAlert.product_id == alert_data.product_id,
        InventoryAlert.store_id == store_id,
        InventoryAlert.alert_type == alert_data.alert_type,
        InventoryAlert.is_resolved == False
    ).first()
    
    if existing:
        return InventoryAlertResponse.from_orm(existing)
    
    new_alert = InventoryAlert(
        product_id=alert_data.product_id,
        store_id=store_id,
        alert_type=alert_data.alert_type,
        current_quantity=alert_data.current_quantity,
        threshold_quantity=alert_data.threshold_quantity,
        message=alert_data.message
    )
    
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    return InventoryAlertResponse.from_orm(new_alert)


@router.put("/inventory-alerts/{alert_id}/resolve", response_model=InventoryAlertResponse)
async def resolve_inventory_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Mark an inventory alert as resolved"""
    
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can resolve alerts"
        )
    
    alert = db.query(InventoryAlert).filter(
        InventoryAlert.id == alert_id,
        InventoryAlert.store_id == store_id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    return InventoryAlertResponse.from_orm(alert)


@router.get("/product/{product_id}/analytics", response_model=List[ProductAnalyticsResponse])
async def get_product_analytics(
    product_id: UUID,
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific product"""
    
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access analytics"
        )
    
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    analytics = db.query(ProductAnalytics).filter(
        ProductAnalytics.product_id == product_id,
        ProductAnalytics.store_id == store_id,
        ProductAnalytics.date >= start_date
    ).order_by(ProductAnalytics.date).all()
    
    return [ProductAnalyticsResponse.from_orm(a) for a in analytics]
