from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False, default=UserRole.CUSTOMER)
    
    # Store relationship for admins
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=True)
    store = relationship("Store", back_populates="admins")
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Relationships
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    referral_codes = relationship("ReferralCode", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_used = relationship("Referral", foreign_keys="Referral.referee_id", back_populates="referee")
    loyalty_points = relationship("LoyaltyPoints", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")

    def __repr__(self):
        return f"<User {self.email} - {self.role}>"

    # ── Convenience role-check properties ─────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        """True for both ADMIN and SUPER_ADMIN roles."""
        return self.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    @property
    def is_superuser(self) -> bool:
        """True only for SUPER_ADMIN role."""
        return self.role == UserRole.SUPER_ADMIN


class Address(Base):
    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Address details
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address_line1 = Column(String(500), nullable=False)
    address_line2 = Column(String(500), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    landmark = Column(String(255), nullable=True)
    
    # Address type
    is_default = Column(Boolean, default=False, nullable=False)
    address_type = Column(String(50), default="home", nullable=False)  # home, work, other
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"<Address {self.city}, {self.pincode}>"


class APIKeyScope(str, enum.Enum):
    """Scopes controlling what an API key can do"""
    READ_PRODUCTS      = "products:read"
    WRITE_PRODUCTS     = "products:write"
    READ_ORDERS        = "orders:read"
    WRITE_ORDERS       = "orders:write"
    READ_INVENTORY     = "inventory:read"
    WRITE_INVENTORY    = "inventory:write"
    SYNC               = "sync:write"
    WEBHOOK            = "webhook:write"
    FULL_ACCESS        = "*"


class APIKey(Base):
    """
    API keys for B2B / POS / sync-agent integrations.
    The raw key is only shown ONCE on creation; only its SHA-256 hash is stored.
    Format:  ec_live_<32-hex>  or  ec_test_<32-hex>
    """
    __tablename__ = "api_keys"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(100), nullable=False)          # human label, e.g. "KasaPOS sync"
    key_hash    = Column(String(64),  nullable=False, unique=True, index=True)  # SHA-256 hex
    key_prefix  = Column(String(16),  nullable=False)          # first 8 chars — for display
    is_test     = Column(Boolean, default=False, nullable=False)

    # Ownership — either a store or a user (super-admin) can own a key
    store_id    = Column(UUID(as_uuid=True), ForeignKey("stores.id"),  nullable=True, index=True)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"),   nullable=True, index=True)

    # Scopes (PostgreSQL array)
    scopes      = Column(ARRAY(String), nullable=False, default=list)

    # Lifecycle
    is_active   = Column(Boolean, default=True,  nullable=False)
    expires_at  = Column(DateTime, nullable=True)              # NULL = never expires
    last_used_at = Column(DateTime, nullable=True)
    request_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at  = Column(DateTime, nullable=True)

    # Relationships
    store = relationship("Store", foreign_keys=[store_id])
    user  = relationship("User",  foreign_keys=[user_id])

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<APIKey {self.key_prefix}... name={self.name!r}>"
