"""
Analytics API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, distinct
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, date
import csv
import io

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
from app.schemas.schemas import APIResponse

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
    
    # ── Single-pass conditional aggregation — one round-trip to Postgres ──────
    # Replaces 4 separate .all() + Python sum/set loops that OOM on large stores.
    stats_row = db.query(
        func.count(Order.id).filter(
            func.date(Order.created_at) == today
        ).label("today_orders"),
        func.coalesce(
            func.sum(Order.total_amount).filter(func.date(Order.created_at) == today), 0
        ).label("today_revenue"),
        func.count(distinct(Order.user_id)).filter(
            func.date(Order.created_at) == today, Order.user_id.isnot(None)
        ).label("today_customers"),
        func.count(Order.id).filter(
            func.date(Order.created_at) == yesterday
        ).label("yesterday_orders"),
        func.coalesce(
            func.sum(Order.total_amount).filter(func.date(Order.created_at) == yesterday), 0
        ).label("yesterday_revenue"),
        func.count(distinct(Order.user_id)).filter(
            func.date(Order.created_at) == yesterday, Order.user_id.isnot(None)
        ).label("yesterday_customers"),
        func.count(Order.id).filter(
            func.date(Order.created_at) >= week_ago
        ).label("week_orders"),
        func.coalesce(
            func.sum(Order.total_amount).filter(func.date(Order.created_at) >= week_ago), 0
        ).label("week_revenue"),
        func.count(distinct(Order.user_id)).filter(
            func.date(Order.created_at) >= week_ago, Order.user_id.isnot(None)
        ).label("week_customers"),
        func.count(Order.id).filter(
            func.date(Order.created_at) >= month_ago
        ).label("month_orders"),
        func.coalesce(
            func.sum(Order.total_amount).filter(func.date(Order.created_at) >= month_ago), 0
        ).label("month_revenue"),
        func.count(distinct(Order.user_id)).filter(
            func.date(Order.created_at) >= month_ago, Order.user_id.isnot(None)
        ).label("month_customers"),
    ).filter(Order.store_id == store_id).one()

    today_orders_count     = stats_row.today_orders or 0
    today_revenue          = float(stats_row.today_revenue or 0)
    today_customers        = stats_row.today_customers or 0
    yesterday_orders_count = stats_row.yesterday_orders or 0
    yesterday_revenue      = float(stats_row.yesterday_revenue or 0)
    yesterday_customers    = stats_row.yesterday_customers or 0
    week_orders_count      = stats_row.week_orders or 0
    week_revenue           = float(stats_row.week_revenue or 0)
    week_customers         = stats_row.week_customers or 0
    month_orders_count     = stats_row.month_orders or 0
    month_revenue          = float(stats_row.month_revenue or 0)
    month_customers        = stats_row.month_customers or 0

    # Calculate % changes vs yesterday
    orders_change    = ((today_orders_count  - yesterday_orders_count)  / yesterday_orders_count  * 100) if yesterday_orders_count  > 0 else 0
    revenue_change   = ((today_revenue       - yesterday_revenue)       / yesterday_revenue       * 100) if yesterday_revenue       > 0 else 0
    customers_change = ((today_customers     - yesterday_customers)     / yesterday_customers     * 100) if yesterday_customers     > 0 else 0
    
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
    
    # If no pre-aggregated analytics, compute on the fly with a single GROUP BY
    if not analytics:
        # One query, not N queries — eliminates the O(N) round-trip loop
        rows = (
            db.query(
                func.date(Order.created_at).label("day"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
                func.count(distinct(Order.user_id)).filter(
                    Order.user_id.isnot(None)
                ).label("customer_count"),
            )
            .filter(
                Order.store_id == store_id,
                func.date(Order.created_at).between(start_date, end_date),
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )
        # Build lookup and fill ALL days including zero-order days
        row_map = {str(r.day): r for r in rows}
        dates, revenue, orders, customers = [], [], [], []
        current_date = start_date
        while current_date <= end_date:
            key = current_date.strftime("%Y-%m-%d")
            r = row_map.get(key)
            dates.append(key)
            orders.append(r.order_count if r else 0)
            revenue.append(round(float(r.total_revenue) if r else 0, 2))
            customers.append(r.customer_count if r else 0)
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


# ── Revenue by Category ───────────────────────────────────────────────────────

@router.get("/revenue-by-category", response_model=APIResponse)
async def revenue_by_category(
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    """Revenue and units sold broken down by product category (last N days)."""
    from app.models.models import Category

    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    since = datetime.utcnow().date() - timedelta(days=days)

    rows = (
        db.query(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.count(distinct(Order.id)).label("order_count"),
            func.sum(OrderItem.quantity).label("units_sold"),
            func.sum(OrderItem.subtotal).label("revenue"),
        )
        .join(Product, Product.category_id == Category.id)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.store_id == store_id,
            func.date(Order.created_at) >= since,
        )
        .group_by(Category.id, Category.name)
        .order_by(desc("revenue"))
        .all()
    )

    data = [
        {
            "category_id": str(r.category_id),
            "category_name": r.category_name,
            "order_count": r.order_count,
            "units_sold": int(r.units_sold or 0),
            "revenue": round(float(r.revenue or 0), 2),
        }
        for r in rows
    ]
    return APIResponse(success=True, data=data, meta={"days": days, "total_categories": len(data)})


# ── Customer Retention / Cohort ───────────────────────────────────────────────

@router.get("/customer-retention", response_model=APIResponse)
async def customer_retention(
    months: int = Query(6, ge=2, le=12),
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    """
    Monthly new-vs-returning customer cohort data (last *months* calendar months).
    Returns a list of monthly buckets with: new_customers, returning_customers,
    retention_rate.
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    today = datetime.utcnow().date()
    result = []

    for i in range(months - 1, -1, -1):
        # Start of month (approx: first day, using 30-day windows)
        month_start = (today.replace(day=1) - timedelta(days=30 * i))
        month_start = month_start.replace(day=1)
        if i == 0:
            month_end = today
        else:
            # last day of that month
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = next_month - timedelta(days=1)

        # Customers who placed an order this month
        month_customers = (
            db.query(Order.user_id)
            .filter(
                Order.store_id == store_id,
                Order.user_id.isnot(None),
                func.date(Order.created_at) >= month_start,
                func.date(Order.created_at) <= month_end,
            )
            .distinct()
            .all()
        )
        month_customer_ids = {str(r.user_id) for r in month_customers}

        if not month_customer_ids:
            result.append({
                "month": month_start.strftime("%Y-%m"),
                "new_customers": 0,
                "returning_customers": 0,
                "retention_rate": 0.0,
            })
            continue

        # Customers who had at least one order BEFORE this month
        returning = (
            db.query(Order.user_id)
            .filter(
                Order.store_id == store_id,
                Order.user_id.in_(month_customer_ids),
                func.date(Order.created_at) < month_start,
            )
            .distinct()
            .all()
        )
        returning_ids = {str(r.user_id) for r in returning}
        returning_count = len(returning_ids)
        new_count = len(month_customer_ids) - returning_count
        total = len(month_customer_ids)
        retention = round(returning_count / total * 100, 1) if total else 0.0

        result.append({
            "month": month_start.strftime("%Y-%m"),
            "new_customers": new_count,
            "returning_customers": returning_count,
            "retention_rate": retention,
        })

    return APIResponse(success=True, data=result, meta={"months": months})


# ── Search Analytics ──────────────────────────────────────────────────────────

@router.get("/search-terms", response_model=APIResponse)
async def search_term_analytics(
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    """Top search queries for this store (sourced from Redis via SearchService)."""
    from app.services.search_service import SearchService

    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    svc = SearchService(db)
    data = await svc.get_search_analytics(str(store_id))
    return APIResponse(success=True, data=data)


# ── CSV Export ────────────────────────────────────────────────────────────────

@router.get("/export/orders", summary="Export orders as CSV")
async def export_orders_csv(
    days: int = Query(30, ge=1, le=365),
    order_status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    store_id: UUID = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    """Stream a CSV file with all orders for the given period."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    since = datetime.utcnow() - timedelta(days=days)

    q = db.query(Order).filter(
        Order.store_id == store_id,
        Order.created_at >= since,
    )
    if order_status:
        q = q.filter(Order.status == order_status)

    orders = q.order_by(Order.created_at.desc()).all()

    def _stream():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "order_number", "created_at", "status", "payment_status",
            "customer_name", "customer_phone", "customer_email",
            "total_amount", "discount_amount", "final_amount",
        ])
        buf.seek(0)
        yield buf.read()

        for o in orders:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                o.order_number,
                o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "",
                o.status,
                o.payment_status,
                getattr(o, "customer_name", "") or "",
                getattr(o, "customer_phone", "") or "",
                getattr(o, "customer_email", "") or "",
                o.total_amount,
                getattr(o, "discount_amount", 0) or 0,
                getattr(o, "final_amount", o.total_amount) or o.total_amount,
            ])
            buf.seek(0)
            yield buf.read()

    filename = f"orders_{store_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        _stream(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


