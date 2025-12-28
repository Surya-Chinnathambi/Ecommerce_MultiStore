"""
Analytics and Metrics Models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, Text, ForeignKey, Index, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class DailyAnalytics(Base):
    """Daily aggregated analytics per store"""
    __tablename__ = "daily_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Sales Metrics
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    total_items_sold = Column(Integer, default=0)
    average_order_value = Column(Float, default=0.0)
    
    # Order Status
    pending_orders = Column(Integer, default=0)
    confirmed_orders = Column(Integer, default=0)
    delivered_orders = Column(Integer, default=0)
    cancelled_orders = Column(Integer, default=0)
    
    # Customer Metrics
    new_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    
    # Product Metrics
    unique_products_sold = Column(Integer, default=0)
    out_of_stock_count = Column(Integer, default=0)
    low_stock_count = Column(Integer, default=0)
    
    # Traffic Metrics
    page_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    
    # Additional metrics as JSON
    metrics = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("Store")
    
    __table_args__ = (
        Index('idx_store_date_analytics', 'store_id', 'date', unique=True),
    )


class ProductAnalytics(Base):
    """Product-level analytics"""
    __tablename__ = "product_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Sales
    units_sold = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    orders_count = Column(Integer, default=0)
    
    # Engagement
    views = Column(Integer, default=0)
    add_to_cart = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    
    # Reviews
    new_reviews = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    store = relationship("Store")
    
    __table_args__ = (
        Index('idx_product_date_analytics', 'product_id', 'date', unique=True),
    )


class InventoryAlert(Base):
    """Inventory alerts for low stock and out of stock"""
    __tablename__ = "inventory_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # 'low_stock', 'out_of_stock', 'critical'
    current_quantity = Column(Integer, nullable=False)
    threshold_quantity = Column(Integer, nullable=False)
    
    # Status
    is_resolved = Column(Boolean, default=False, index=True)
    is_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Message
    message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    store = relationship("Store")
    
    __table_args__ = (
        Index('idx_store_unresolved', 'store_id', 'is_resolved'),
        Index('idx_product_type', 'product_id', 'alert_type'),
    )
