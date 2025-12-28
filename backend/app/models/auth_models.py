from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
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
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    
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
    # TODO: Uncomment when user_id column is added to orders table
    # orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    referral_codes = relationship("ReferralCode", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_used = relationship("Referral", foreign_keys="Referral.referee_id", back_populates="referee")
    loyalty_points = relationship("LoyaltyPoints", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} - {self.role}>"


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
