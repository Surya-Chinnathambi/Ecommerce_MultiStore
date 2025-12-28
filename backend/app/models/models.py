"""
Multi-Tenant Database Models
Implements enterprise-scale data models with partitioning support
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


# Enums
class StoreStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class StoreTier(str, enum.Enum):
    TIER1 = "tier1"  # High activity
    TIER2 = "tier2"  # Medium activity
    TIER3 = "tier3"  # Low activity
    TIER4 = "tier4"  # Inactive/Trial


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COD = "cod"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# Models
class Store(Base):
    """Store/Tenant model - each retail store is a tenant"""
    __tablename__ = "stores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)  # From billing system
    
    # Basic Info
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)  # URL-friendly name
    domain = Column(String(255), unique=True, index=True)  # Custom domain
    
    # Contact
    owner_name = Column(String(200))
    owner_phone = Column(String(20), index=True)
    owner_email = Column(String(255), index=True)
    address = Column(Text)
    city = Column(String(100), index=True)
    state = Column(String(100))
    pincode = Column(String(10), index=True)
    
    # Business Settings
    currency = Column(String(3), default="INR")
    timezone = Column(String(50), default="Asia/Kolkata")
    language = Column(String(10), default="en")
    
    # Sync Configuration
    sync_tier = Column(SQLEnum(StoreTier), default=StoreTier.TIER3, index=True)
    sync_interval_minutes = Column(Integer, default=30)
    last_sync_at = Column(DateTime, index=True)
    sync_api_key = Column(String(255), unique=True, nullable=False)  # For sync agent auth
    
    # Status
    status = Column(SQLEnum(StoreStatus), default=StoreStatus.TRIAL, index=True)
    is_active = Column(Boolean, default=True, index=True)
    trial_ends_at = Column(DateTime)
    subscription_ends_at = Column(DateTime)
    
    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#000000")
    secondary_color = Column(String(7), default="#FFFFFF")
    
    # Settings
    settings = Column(JSONB, default={})  # Flexible JSON for store-specific settings
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="store", cascade="all, delete-orphan")
    admins = relationship("User", back_populates="store", foreign_keys="User.store_id")
    banners = relationship("PromotionalBanner", back_populates="store")
    flash_sales = relationship("FlashSale", back_populates="store")
    social_activities = relationship("SocialProofActivity", back_populates="store")
    referral_codes = relationship("ReferralCode", back_populates="store")

    __table_args__ = (
        Index('idx_store_status_tier', 'status', 'sync_tier'),
        Index('idx_store_domain', 'domain'),
    )
class Category(Base):
    """Product categories per store"""
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("Store", back_populates="categories")
    products = relationship("Product", back_populates="category")
    
    __table_args__ = (
        Index('idx_category_store_slug', 'store_id', 'slug', unique=True),
        Index('idx_category_store_active', 'store_id', 'is_active'),
    )


class Product(Base):
    """Product model - partitioned by store_id for scale"""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(100), nullable=False, index=True)  # ID from billing system
    
    # Basic Info
    name = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))
    
    # Category
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    
    # Pricing
    mrp = Column(Float, nullable=False)  # Maximum Retail Price
    selling_price = Column(Float, nullable=False, index=True)
    discount_percent = Column(Float, default=0)
    cost_price = Column(Float)  # For profit calculation
    
    # Inventory
    quantity = Column(Integer, default=0, index=True)
    low_stock_threshold = Column(Integer, default=10)
    unit = Column(String(50))  # kg, liter, piece, etc.
    
    # Product Details
    sku = Column(String(100), index=True)
    barcode = Column(String(100), index=True)
    hsn_code = Column(String(20))  # Tax classification
    gst_percent = Column(Float, default=0)
    
    # Media
    images = Column(JSONB, default=[])  # Array of image URLs
    thumbnail = Column(String(500))
    
    # SEO
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    meta_keywords = Column(String(500))
    
    # Attributes (flexible JSON)
    attributes = Column(JSONB, default={})  # Size, color, weight, etc.
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_in_stock = Column(Boolean, default=True, index=True)
    
    # Sync Metadata
    last_synced_at = Column(DateTime, index=True)
    sync_version = Column(Integer, default=1)  # For version tracking
    sync_checksum = Column(String(64))  # MD5/SHA256 for change detection
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    flash_sales = relationship("FlashSale", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_product_store_external', 'store_id', 'external_id', unique=True),
        Index('idx_product_store_active', 'store_id', 'is_active'),
        Index('idx_product_store_stock', 'store_id', 'is_in_stock'),
        Index('idx_product_updated', 'store_id', 'updated_at'),
        Index('idx_product_search', 'store_id', 'name'),  # For search
    )


class Order(Base):
    """Customer orders - partitioned by store_id and created_at"""
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer Info
    # TODO: Add user_id column to database
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_name = Column(String(200), nullable=False)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_email = Column(String(255), nullable=True)
    
    # Delivery Address
    delivery_address = Column(Text, nullable=False)
    delivery_city = Column(String(100))
    delivery_state = Column(String(100))
    delivery_pincode = Column(String(10), index=True)
    delivery_landmark = Column(String(200))
    
    # Order Details
    order_status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.COD, nullable=False, index=True)
    payment_method = Column(String(50), default="COD")
    
    # Pricing
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    delivery_charge = Column(Float, default=0)
    total_amount = Column(Float, nullable=False, index=True)
    
    # Additional Info
    notes = Column(Text)
    internal_notes = Column(Text)  # Not visible to customer
    
    # Delivery
    expected_delivery_date = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Metadata
    ip_address = Column(String(50))
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("Store", back_populates="orders")
    # TODO: Uncomment when user_id column is added to database
    # user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_order_store_status', 'store_id', 'order_status'),
        Index('idx_order_store_date', 'store_id', 'created_at'),
        Index('idx_order_customer', 'store_id', 'customer_phone'),
    )


class OrderItem(Base):
    """Individual items in an order"""
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Product snapshot at time of order
    product_name = Column(String(500), nullable=False)
    product_sku = Column(String(100))
    product_image = Column(String(500))
    
    # Pricing snapshot
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)
    tax_percent = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    total = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class SyncLog(Base):
    """Track synchronization operations for monitoring"""
    __tablename__ = "sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sync_type = Column(String(50), nullable=False)  # full, delta, inventory_only
    status = Column(String(50), nullable=False, index=True)  # success, partial, failed
    
    records_received = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    duration_seconds = Column(Float)
    error_message = Column(Text)
    error_details = Column(JSONB)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_sync_log_store_date', 'store_id', 'started_at'),
    )
