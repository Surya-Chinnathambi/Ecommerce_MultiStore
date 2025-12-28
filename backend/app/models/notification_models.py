"""
Notification Models
Handles email, SMS, and push notifications
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, enum.Enum):
    """Notification delivery statuses"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationTemplate(Base):
    """Notification templates for different events"""
    __tablename__ = "notification_templates"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Store (optional - null means global template)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    
    # Template Details
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(100), nullable=False, unique=True, index=True)  # e.g., ORDER_CONFIRMED
    description = Column(Text)
    
    # Content
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    
    # Email specific
    subject = Column(String(500))  # For email
    html_body = Column(Text)
    text_body = Column(Text)
    
    # SMS specific
    sms_body = Column(Text)  # For SMS (160 chars recommended)
    
    # Push notification specific
    push_title = Column(String(200))
    push_body = Column(String(500))
    
    # Template Variables (JSON)
    variables = Column(JSONB, default=[])  # List of variable names: ["order_number", "customer_name"]
    
    # Settings
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="notification_templates")
    
    __table_args__ = (
        Index('idx_template_code_type', 'code', 'notification_type'),
        Index('idx_template_store_active', 'store_id', 'is_active'),
    )


class Notification(Base):
    """Individual notification records"""
    __tablename__ = "notifications"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id", ondelete="SET NULL"), index=True)
    
    # Related Entities (optional)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), index=True)
    
    # Notification Details
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Recipient Info
    recipient_email = Column(String(255), index=True)
    recipient_phone = Column(String(20), index=True)
    recipient_name = Column(String(200))
    
    # Content
    subject = Column(String(500))
    body = Column(Text)
    html_body = Column(Text)
    
    # Delivery Details
    provider = Column(String(50))  # sendgrid, twilio, fcm, etc.
    provider_message_id = Column(String(255), index=True)
    provider_response = Column(JSONB)
    
    # Tracking
    sent_at = Column(DateTime, index=True)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    failed_at = Column(DateTime)
    
    # Error Handling
    error_message = Column(Text)
    error_code = Column(String(50))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Template Data
    template_variables = Column(JSONB, default={})  # Variables used to render template
    
    # Metadata
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="notifications")
    user = relationship("User", backref="notifications")
    template = relationship("NotificationTemplate", backref="notifications")
    
    __table_args__ = (
        Index('idx_notification_store_status', 'store_id', 'status'),
        Index('idx_notification_type_status', 'notification_type', 'status'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_user', 'user_id', 'created_at'),
    )


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Email Preferences
    email_enabled = Column(Boolean, default=True)
    email_order_updates = Column(Boolean, default=True)
    email_payment_updates = Column(Boolean, default=True)
    email_shipping_updates = Column(Boolean, default=True)
    email_promotions = Column(Boolean, default=False)
    email_newsletter = Column(Boolean, default=False)
    
    # SMS Preferences
    sms_enabled = Column(Boolean, default=True)
    sms_order_updates = Column(Boolean, default=True)
    sms_payment_updates = Column(Boolean, default=True)
    sms_shipping_updates = Column(Boolean, default=True)
    sms_promotions = Column(Boolean, default=False)
    
    # Push Notification Preferences
    push_enabled = Column(Boolean, default=True)
    push_order_updates = Column(Boolean, default=True)
    push_payment_updates = Column(Boolean, default=True)
    push_shipping_updates = Column(Boolean, default=True)
    push_promotions = Column(Boolean, default=False)
    
    # In-App Preferences
    in_app_enabled = Column(Boolean, default=True)
    
    # Quiet Hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5))  # Format: "22:00"
    quiet_hours_end = Column(String(5))    # Format: "08:00"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="notification_preference", uselist=False)


class NotificationLog(Base):
    """Audit log for all notification events"""
    __tablename__ = "notification_logs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign Key
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event Details
    event_type = Column(String(50), nullable=False, index=True)  # sent, delivered, opened, clicked, failed, bounced
    event_data = Column(JSONB)
    
    # Provider Info
    provider = Column(String(50))
    provider_event_id = Column(String(255))
    
    # Timestamp
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    notification = relationship("Notification", backref="logs")
    
    __table_args__ = (
        Index('idx_log_notification_event', 'notification_id', 'event_type'),
        Index('idx_log_occurred', 'occurred_at'),
    )
