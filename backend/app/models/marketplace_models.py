"""
Marketplace & Flipkart-parity Models
Covers: Product Variants, Wishlist, Sellers, Returns, Coupons, Pincode Delivery
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class VariantType(str, enum.Enum):
    SIZE      = "size"
    COLOR     = "color"
    STORAGE   = "storage"
    RAM       = "ram"
    WEIGHT    = "weight"
    PACK_SIZE = "pack_size"
    CUSTOM    = "custom"


class SellerStatus(str, enum.Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    SUSPENDED = "suspended"
    REJECTED  = "rejected"


class ReturnStatus(str, enum.Enum):
    REQUESTED   = "requested"
    APPROVED    = "approved"
    PICKED_UP   = "picked_up"
    INSPECTED   = "inspected"
    REFUNDED    = "refunded"
    REJECTED    = "rejected"
    CLOSED      = "closed"


class ReturnReason(str, enum.Enum):
    DEFECTIVE          = "defective"
    WRONG_ITEM         = "wrong_item"
    NOT_AS_DESCRIBED   = "not_as_described"
    CHANGED_MIND       = "changed_mind"
    DAMAGED_IN_TRANSIT = "damaged_in_transit"
    MISSING_PARTS      = "missing_parts"
    OTHER              = "other"


class CouponType(str, enum.Enum):
    PERCENT        = "percent"       # % discount
    FLAT           = "flat"          # fixed INR off
    FREE_SHIPPING  = "free_shipping"
    BUY_X_GET_Y    = "buy_x_get_y"


class PayoutStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


# ─────────────────────────────────────────────
# PRODUCT VARIANTS
# ─────────────────────────────────────────────

class ProductVariantGroup(Base):
    """
    Groups variants for a product, e.g. "Color" or "Storage".
    A product can have multiple groups (Color + RAM).
    """
    __tablename__ = "product_variant_groups"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    store_id   = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    name          = Column(String(100), nullable=False)   # "Color", "Size"
    variant_type  = Column(SQLEnum(VariantType, values_callable=lambda obj: [e.value for e in obj], create_type=False), default=VariantType.CUSTOM)
    display_order = Column(Integer, default=0)

    # Relationships
    variants = relationship("ProductVariant", back_populates="group",
                            cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_pvg_product", "product_id"),
    )


class ProductVariant(Base):
    """
    A single variant option, e.g. "Red / 128 GB".
    Carries its own price, stock and images.
    """
    __tablename__ = "product_variants"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("product_variant_groups.id",
                         ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    store_id   = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    # Value
    value         = Column(String(100), nullable=False)   # "Red", "128 GB"
    display_label = Column(String(100))                   # Optional prettier label
    color_hex     = Column(String(7))                     # For color swatches

    # Variant-specific pricing (overrides parent if set)
    mrp           = Column(Float)
    selling_price = Column(Float)
    discount_pct  = Column(Float)

    # Variant-specific inventory
    sku      = Column(String(100), index=True)
    quantity = Column(Integer, default=0)
    is_in_stock = Column(Boolean, default=True, index=True)

    # Variant-specific images (JSON list of URLs)
    images = Column(JSONB, default=[])

    display_order = Column(Integer, default=0)
    is_active     = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("ProductVariantGroup", back_populates="variants")

    __table_args__ = (
        Index("idx_pv_product_active", "product_id", "is_active"),
        UniqueConstraint("product_id", "group_id", "value", name="uq_variant_value"),
    )


# ─────────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────────

class WishlistItem(Base):
    """Persistent wishlist — one row per (user, product)."""
    __tablename__ = "wishlist_items"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    store_id   = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id",
                         ondelete="SET NULL"), nullable=True)

    added_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product")
    variant = relationship("ProductVariant")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
        Index("idx_wishlist_user", "user_id"),
        Index("idx_wishlist_store", "store_id"),
    )


# ─────────────────────────────────────────────
# SELLER / MARKETPLACE
# ─────────────────────────────────────────────

class Seller(Base):
    """
    A seller on the marketplace.
    One User can own one Seller profile (role=SELLER).
    """
    __tablename__ = "sellers"

    id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"),
                     nullable=False, unique=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                      nullable=False, index=True)

    # Business identity
    business_name      = Column(String(300), nullable=False)
    business_type      = Column(String(50))                 # individual / pvt_ltd / llp
    gstin              = Column(String(20), index=True)
    pan                = Column(String(20))
    fssai_number       = Column(String(20))                 # for food sellers

    # Address
    address_line1 = Column(String(300))
    address_line2 = Column(String(300))
    city          = Column(String(100))
    state         = Column(String(100))
    pincode       = Column(String(10))

    # Bank / payout
    bank_account_number = Column(String(50))
    bank_ifsc           = Column(String(20))
    bank_account_name   = Column(String(200))
    upi_id              = Column(String(100))

    # Marketplace settings
    commission_rate   = Column(Float, default=5.0)   # platform fee %
    payout_cycle_days = Column(Integer, default=7)   # weekly by default

    # Status
    status               = Column(SQLEnum(SellerStatus, values_callable=lambda obj: [e.value for e in obj], create_type=False), default=SellerStatus.PENDING, index=True)
    is_active            = Column(Boolean, default=False, index=True)
    kyc_verified         = Column(Boolean, default=False)
    kyc_documents        = Column(JSONB, default=[])   # S3 keys of uploaded docs

    # Ratings aggregated
    avg_rating      = Column(Float, default=0.0)
    total_ratings   = Column(Integer, default=0)
    total_orders    = Column(Integer, default=0)
    total_returns   = Column(Integer, default=0)

    # Timestamps
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at  = Column(DateTime)

    # Relationships
    products = relationship("SellerProduct", back_populates="seller",
                            cascade="all, delete-orphan")
    payouts  = relationship("SellerPayout", back_populates="seller",
                            cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_seller_status", "status", "is_active"),
    )


class SellerProduct(Base):
    """
    Maps a Seller to a Product with seller-specific price, stock, fulfilment.
    Multiple sellers can sell the same product at different prices.
    """
    __tablename__ = "seller_products"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id  = Column(UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    store_id   = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    selling_price = Column(Float, nullable=False)
    mrp           = Column(Float, nullable=False)
    quantity      = Column(Integer, default=0)
    is_in_stock   = Column(Boolean, default=True, index=True)
    is_active     = Column(Boolean, default=True, index=True)

    # Fulfilment
    dispatch_days     = Column(Integer, default=2)   # promised dispatch SLA
    return_days       = Column(Integer, default=7)
    warranty_months   = Column(Integer, default=0)

    # Rank (lower = shown first for this product)
    display_rank = Column(Integer, default=100)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    seller  = relationship("Seller", back_populates="products")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("seller_id", "product_id", name="uq_seller_product"),
        Index("idx_sp_product_active", "product_id", "is_active"),
    )


class SellerPayout(Base):
    """Settlement record: platform pays seller periodically."""
    __tablename__ = "seller_payouts"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id    = Column(UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="RESTRICT"),
                          nullable=False, index=True)
    store_id     = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="RESTRICT"),
                          nullable=False, index=True)

    period_start  = Column(DateTime, nullable=False)
    period_end    = Column(DateTime, nullable=False)
    gross_amount  = Column(Float, default=0.0)
    commission    = Column(Float, default=0.0)
    refund_deductions = Column(Float, default=0.0)
    net_amount    = Column(Float, default=0.0)

    status           = Column(SQLEnum(PayoutStatus, values_callable=lambda obj: [e.value for e in obj], create_type=False), default=PayoutStatus.PENDING, index=True)
    payment_ref      = Column(String(100))        # UTR / transaction id
    payment_method   = Column(String(50))         # NEFT / UPI
    paid_at          = Column(DateTime)

    orders_count  = Column(Integer, default=0)
    returns_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    seller = relationship("Seller", back_populates="payouts")

    __table_args__ = (
        Index("idx_payout_seller_status", "seller_id", "status"),
    )


# ─────────────────────────────────────────────
# RETURNS & REFUNDS
# ─────────────────────────────────────────────

class ReturnRequest(Base):
    """Customer initiates a return/refund for one or more items."""
    __tablename__ = "return_requests"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id     = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"),
                          nullable=False, index=True)
    store_id     = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
                          index=True)

    return_number = Column(String(50), unique=True, nullable=False, index=True)

    reason        = Column(SQLEnum(ReturnReason, values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    description   = Column(Text)
    images        = Column(JSONB, default=[])     # customer-uploaded proof photos

    status         = Column(SQLEnum(ReturnStatus, values_callable=lambda obj: [e.value for e in obj], create_type=False), default=ReturnStatus.REQUESTED, index=True)
    admin_notes    = Column(Text)
    rejection_reason = Column(Text)

    # Pickup / logistics
    pickup_scheduled_at = Column(DateTime)
    pickup_completed_at = Column(DateTime)
    tracking_id         = Column(String(100))

    # Refund
    refund_amount   = Column(Float)
    refund_method   = Column(String(50))     # original / wallet / upi
    refund_ref      = Column(String(100))
    refunded_at     = Column(DateTime)

    requested_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at   = Column(DateTime)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items  = relationship("ReturnItem", back_populates="return_request",
                          cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_return_order", "order_id"),
        Index("idx_return_store_status", "store_id", "status"),
        Index("idx_return_user", "user_id"),
    )


class ReturnItem(Base):
    """Individual items within a return request."""
    __tablename__ = "return_items"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_request_id = Column(UUID(as_uuid=True), ForeignKey("return_requests.id",
                                ondelete="CASCADE"), nullable=False, index=True)
    order_item_id    = Column(UUID(as_uuid=True), ForeignKey("order_items.id",
                               ondelete="RESTRICT"), nullable=False, index=True)

    product_name     = Column(String(500), nullable=False)
    quantity         = Column(Integer, nullable=False)
    unit_price       = Column(Float, nullable=False)
    refund_amount    = Column(Float)

    # Relationships
    return_request = relationship("ReturnRequest", back_populates="items")

    __table_args__ = (
        Index("idx_ri_return_request", "return_request_id"),
    )


# ─────────────────────────────────────────────
# COUPONS & PROMOTIONS
# ─────────────────────────────────────────────

class Coupon(Base):
    """Discount coupon / promo code."""
    __tablename__ = "coupons"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                      nullable=False, index=True)

    code          = Column(String(50), nullable=False)
    description   = Column(String(500))
    coupon_type   = Column(SQLEnum(CouponType, values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False, default=CouponType.PERCENT)

    # Discount values
    discount_value   = Column(Float, nullable=False)   # % or flat amount
    max_discount_cap = Column(Float)                   # ceiling for percent discounts

    # Buy X Get Y
    buy_quantity = Column(Integer)   # buy X
    get_quantity = Column(Integer)   # get Y free

    # Conditions
    min_order_amount = Column(Float, default=0.0)
    max_uses_total   = Column(Integer)          # None = unlimited
    max_uses_per_user = Column(Integer, default=1)
    applicable_category_ids = Column(JSONB, default=[])  # empty = all categories
    applicable_product_ids  = Column(JSONB, default=[])  # empty = all products

    # Validity
    valid_from    = Column(DateTime, nullable=False)
    valid_until   = Column(DateTime, nullable=False, index=True)
    is_active     = Column(Boolean, default=True, index=True)

    # Counters (denormalised for speed)
    used_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usages = relationship("CouponUsage", back_populates="coupon",
                          cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("store_id", "code", name="uq_coupon_store_code"),
        Index("idx_coupon_store_active", "store_id", "is_active"),
    )


class CouponUsage(Base):
    """Tracks each application of a coupon."""
    __tablename__ = "coupon_usages"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id  = Column(UUID(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
                        index=True)
    order_id   = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"),
                        index=True)
    store_id   = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    discount_applied = Column(Float, nullable=False)
    used_at          = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    coupon = relationship("Coupon", back_populates="usages")

    __table_args__ = (
        Index("idx_cu_coupon_user", "coupon_id", "user_id"),
    )


# ─────────────────────────────────────────────
# PINCODE DELIVERY ESTIMATOR
# ─────────────────────────────────────────────

class PincodeDelivery(Base):
    """
    Delivery availability and ETA by pincode.
    Populated via a cron job from logistics partner APIs.
    """
    __tablename__ = "pincode_delivery"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id     = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    pincode      = Column(String(10), nullable=False, index=True)

    city         = Column(String(100))
    state        = Column(String(100))
    is_serviceable = Column(Boolean, default=True, index=True)

    # Estimated delivery days from today
    standard_days    = Column(Integer, default=5)
    express_days     = Column(Integer)           # None = express not available
    same_day         = Column(Boolean, default=False)

    cod_available    = Column(Boolean, default=True)
    prepaid_only     = Column(Boolean, default=False)

    # Logistics partner
    courier_partner  = Column(String(100))

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("store_id", "pincode", name="uq_pincode_store"),
        Index("idx_pincode_serviceable", "store_id", "is_serviceable"),
    )

