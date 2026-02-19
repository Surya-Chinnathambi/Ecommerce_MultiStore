"""
Analytics Celery tasks
"""
from celery import Task
from datetime import datetime, timedelta
import logging

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.models import Store, Order, Product
from app.models.analytics_models import DailyAnalytics, InventoryAlert
from sqlalchemy import func, and_, distinct

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.analytics_tasks.generate_daily_analytics")
def generate_daily_analytics(self):
    """
    Generate daily analytics for all stores
    Runs at 1 AM daily
    """
    logger.info("Generating daily analytics...")
    
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    start_datetime = datetime.combine(yesterday, datetime.min.time())
    end_datetime = datetime.combine(yesterday, datetime.max.time())
    
    stores = self.db.query(Store).filter(Store.is_active == True).all()
    
    for store in stores:
        try:
            # Calculate daily metrics
            orders = self.db.query(Order).filter(
                and_(
                    Order.store_id == store.id,
                    Order.created_at >= start_datetime,
                    Order.created_at <= end_datetime
                )
            ).all()
            
            total_orders = len(orders)
            total_revenue = sum(o.total_amount for o in orders)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Count orders by status
            pending = sum(1 for o in orders if o.status == 'pending')
            confirmed = sum(1 for o in orders if o.status == 'confirmed')
            delivered = sum(1 for o in orders if o.status == 'delivered')
            cancelled = sum(1 for o in orders if o.status == 'cancelled')
            
            # Count unique customers
            user_ids = set(o.user_id for o in orders if o.user_id)
            total_customers = len(user_ids)
            
            # Inventory counts
            out_of_stock = self.db.query(Product).filter(
                Product.store_id == store.id,
                Product.quantity == 0,
                Product.is_active == True
            ).count()
            
            low_stock = self.db.query(Product).filter(
                Product.store_id == store.id,
                Product.quantity > 0,
                Product.quantity < 10,
                Product.is_active == True
            ).count()
            
            # Check if analytics already exists
            existing = self.db.query(DailyAnalytics).filter(
                DailyAnalytics.store_id == store.id,
                DailyAnalytics.date == yesterday
            ).first()
            
            if existing:
                # Update existing
                existing.total_orders = total_orders
                existing.total_revenue = total_revenue
                existing.average_order_value = avg_order_value
                existing.pending_orders = pending
                existing.confirmed_orders = confirmed
                existing.delivered_orders = delivered
                existing.cancelled_orders = cancelled
                existing.total_customers = total_customers
                existing.out_of_stock_count = out_of_stock
                existing.low_stock_count = low_stock
                existing.updated_at = datetime.utcnow()
            else:
                # Create new
                analytics = DailyAnalytics(
                    store_id=store.id,
                    date=yesterday,
                    total_orders=total_orders,
                    total_revenue=total_revenue,
                    average_order_value=avg_order_value,
                    pending_orders=pending,
                    confirmed_orders=confirmed,
                    delivered_orders=delivered,
                    cancelled_orders=cancelled,
                    total_customers=total_customers,
                    out_of_stock_count=out_of_stock,
                    low_stock_count=low_stock
                )
                self.db.add(analytics)
            
            self.db.commit()
            
            logger.info(
                f"Store {store.name} - Orders: {total_orders}, "
                f"Revenue: {total_revenue}, AOV: {avg_order_value}"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate analytics for store {store.id}: {e}")
            self.db.rollback()
    
    logger.info("Daily analytics generation complete")
    return {"processed": len(stores)}


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.analytics_tasks.check_inventory_alerts")
def check_inventory_alerts(self):
    """
    Check inventory levels and create alerts for low/out of stock
    Runs every hour
    """
    logger.info("Checking inventory alerts...")
    
    stores = self.db.query(Store).filter(Store.is_active == True).all()
    alerts_created = 0
    
    for store in stores:
        try:
            # Get all products
            products = self.db.query(Product).filter(
                Product.store_id == store.id,
                Product.is_active == True
            ).all()
            
            for product in products:
                alert_type = None
                threshold = 10  # Default low stock threshold
                
                if product.quantity == 0:
                    alert_type = "out_of_stock"
                    threshold = 0
                elif product.quantity < 5:
                    alert_type = "critical"
                    threshold = 5
                elif product.quantity < 10:
                    alert_type = "low_stock"
                    threshold = 10
                
                if alert_type:
                    # Check if unresolved alert already exists
                    existing = self.db.query(InventoryAlert).filter(
                        InventoryAlert.product_id == product.id,
                        InventoryAlert.store_id == store.id,
                        InventoryAlert.alert_type == alert_type,
                        InventoryAlert.is_resolved == False
                    ).first()
                    
                    if not existing:
                        # Create new alert
                        message = f"{product.name} (SKU: {product.sku}) is {alert_type.replace('_', ' ')}"
                        new_alert = InventoryAlert(
                            product_id=product.id,
                            store_id=store.id,
                            alert_type=alert_type,
                            current_quantity=product.quantity,
                            threshold_quantity=threshold,
                            message=message
                        )
                        self.db.add(new_alert)
                        alerts_created += 1
                        
                        logger.info(f"Created alert: {message}")
                else:
                    # Product has good stock, resolve any existing alerts
                    existing_alerts = self.db.query(InventoryAlert).filter(
                        InventoryAlert.product_id == product.id,
                        InventoryAlert.store_id == store.id,
                        InventoryAlert.is_resolved == False
                    ).all()
                    
                    for alert in existing_alerts:
                        alert.is_resolved = True
                        alert.resolved_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to check inventory for store {store.id}: {e}")
            self.db.rollback()
    
    logger.info(f"Inventory alert check complete. Created {alerts_created} new alerts.")
    return {"alerts_created": alerts_created}


@celery_app.task(name="app.tasks.analytics_tasks.track_product_view")
def track_product_view(store_id: str, product_id: str, session_id: str):
    """
    Track product view for analytics
    """
    return {"success": True}


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.analytics_tasks.update_product_popularity")
def update_product_popularity(self):
    """
    Compute a popularity score for every active product and push the updated
    scores into the Typesense search index.

    Score formula (weights sum to 1):
      0.50 * units_sold_30d (normalised)
    + 0.30 * order_frequency_30d (normalised)
    + 0.20 * average_rating

    Runs every 6 hours via Celery Beat.
    """
    from app.models.models import OrderItem
    from app.services import search_indexer

    logger.info("Updating product popularity scores...")

    stores = self.db.query(Store).filter(Store.is_active == True).all()
    total_updated = 0

    for store in stores:
        try:
            since = datetime.utcnow() - timedelta(days=30)

            # Per-product order stats (last 30 days)
            rows = (
                self.db.query(
                    OrderItem.product_id,
                    func.sum(OrderItem.quantity).label("units_sold"),
                    func.count(func.distinct(Order.id)).label("order_count"),
                )
                .join(Order, Order.id == OrderItem.order_id)
                .filter(
                    Order.store_id == store.id,
                    Order.created_at >= since,
                )
                .group_by(OrderItem.product_id)
                .all()
            )

            if not rows:
                continue

            # Normalise: find max values to scale to [0, 1]
            max_units = max((r.units_sold or 0 for r in rows), default=1) or 1
            max_orders = max((r.order_count or 0 for r in rows), default=1) or 1

            stats = {
                str(r.product_id): {
                    "units_sold": float(r.units_sold or 0),
                    "order_count": float(r.order_count or 0),
                }
                for r in rows
            }

            # Load products that appeared in orders
            products = (
                self.db.query(Product)
                .filter(
                    Product.store_id == store.id,
                    Product.is_active == True,
                    Product.id.in_(list(stats.keys())),
                )
                .all()
            )

            for product in products:
                pid = str(product.id)
                s = stats.get(pid, {})
                units_norm = s.get("units_sold", 0) / max_units
                orders_norm = s.get("order_count", 0) / max_orders
                rating_norm = float(getattr(product, "average_rating", 0) or 0) / 5.0

                score = round(
                    0.50 * units_norm + 0.30 * orders_norm + 0.20 * rating_norm,
                    6,
                )

                # Push to Typesense (fire-and-forget; failures are logged)
                try:
                    search_indexer.update_popularity(str(product.id), score)
                except Exception as ts_err:
                    logger.debug(f"[Popularity] Typesense update skipped: {ts_err}")

                total_updated += 1

        except Exception as exc:
            logger.error(f"[Popularity] Store {store.id} failed: {exc}")
            self.db.rollback()

    logger.info(f"Popularity update complete: {total_updated} products updated")
    return {"updated": total_updated}
