"""
Payment Models
Handles payment transactions, gateways, and refunds
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class PaymentGateway(str, enum.Enum):
    """Supported payment gateways"""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    COD = "cod"  # Cash on Delivery
    MANUAL = "manual"  # Manual bank transfer


class PaymentStatus(str, enum.Enum):
    """Payment transaction statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class RefundStatus(str, enum.Enum):
    """Refund statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class Payment(Base):
    """Payment transactions table"""
    __tablename__ = "payments"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Payment Details
    payment_gateway = Column(SQLEnum(PaymentGateway), nullable=False, index=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    # Amount
    amount = Column(Float, nullable=False)  # Total payment amount
    currency = Column(String(3), default="INR", nullable=False)
    
    # Gateway References
    gateway_payment_id = Column(String(255), index=True)  # Stripe/Razorpay payment ID
    gateway_order_id = Column(String(255), index=True)  # Gateway's order reference
    gateway_signature = Column(String(500))  # For webhook verification
    
    # Payment Method
    payment_method = Column(String(50))  # card, upi, netbanking, wallet, cod
    card_last4 = Column(String(4))  # Last 4 digits of card
    card_brand = Column(String(20))  # visa, mastercard, amex, etc.
    
    # Transaction Details
    transaction_fee = Column(Float, default=0.0)  # Gateway charges
    net_amount = Column(Float)  # Amount after fees
    
    # Customer Details (for gateway)
    customer_email = Column(String(255))
    customer_phone = Column(String(20))
    customer_name = Column(String(200))
    
    # Billing Address
    billing_address = Column(JSONB)  # Flexible JSON for address
    
    # Gateway Response
    gateway_response = Column(JSONB)  # Full response from gateway
    error_message = Column(Text)  # Error details if failed
    error_code = Column(String(50))  # Error code from gateway
    
    # Metadata
    meta_data = Column(JSONB, default={})  # Additional custom data
    notes = Column(Text)  # Internal notes
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    failed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="payments")
    order = relationship("Order", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_payment_store_status', 'store_id', 'status'),
        Index('idx_payment_order', 'order_id'),
        Index('idx_payment_gateway_ref', 'gateway_payment_id', 'gateway_order_id'),
        Index('idx_payment_created', 'created_at'),
    )


class Refund(Base):
    """Refund transactions table"""
    __tablename__ = "refunds"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Refund Details
    status = Column(SQLEnum(RefundStatus), default=RefundStatus.PENDING, nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Refund amount
    currency = Column(String(3), default="INR", nullable=False)
    reason = Column(Text)  # Reason for refund
    
    # Gateway References
    gateway_refund_id = Column(String(255), index=True)  # Stripe/Razorpay refund ID
    gateway_response = Column(JSONB)  # Full response from gateway
    
    # Processing
    initiated_by = Column(String(100))  # admin, customer, system
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))  # Admin who approved
    
    # Error Handling
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Metadata
    meta_data = Column(JSONB, default={})  # Additional custom data
    notes = Column(Text)  # Internal notes
    
    # Timestamps
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    failed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    store = relationship("Store", backref="refunds")
    order = relationship("Order", backref="refunds")
    
    # Indexes
    __table_args__ = (
        Index('idx_refund_payment', 'payment_id'),
        Index('idx_refund_store_status', 'store_id', 'status'),
        Index('idx_refund_created', 'created_at'),
    )


class PaymentWebhook(Base):
    """Webhook events from payment gateways"""
    __tablename__ = "payment_webhooks"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Gateway Details
    gateway = Column(SQLEnum(PaymentGateway), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # payment.success, payment.failed, etc.
    event_id = Column(String(255), unique=True, index=True)  # Gateway's event ID
    
    # Payload
    payload = Column(JSONB, nullable=False)  # Full webhook payload
    signature = Column(String(500))  # Webhook signature for verification
    
    # Processing
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Related Records
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), index=True)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_gateway_event', 'gateway', 'event_type'),
        Index('idx_webhook_processed', 'processed', 'received_at'),
    )
