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
from sqlalchemy import func, and_

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
    # Implementation:
    # - Store in time-series database (TimescaleDB)
    # - Send to analytics platform (Google Analytics, Mixpanel)
    
    return {"success": True}

