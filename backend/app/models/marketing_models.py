from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum
from app.core.database import Base


class BannerType(str, enum.Enum):
    HERO = "hero"
    PROMOTIONAL = "promotional"
    CATEGORY = "category"
    FLASH_SALE = "flash_sale"


class BannerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCHEDULED = "scheduled"


class PromotionalBanner(Base):
    __tablename__ = "promotional_banners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(500))
    description = Column(Text)
    image_url = Column(String(500))
    link_url = Column(String(500))
    banner_type = Column(SQLEnum(BannerType), default=BannerType.PROMOTIONAL)
    status = Column(SQLEnum(BannerStatus), default=BannerStatus.ACTIVE)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    display_order = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="banners")


class FlashSale(Base):
    __tablename__ = "flash_sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    original_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    discount_percent = Column(Float)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    max_quantity = Column(Integer)  # Total items available for sale
    sold_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="flash_sales")
    product = relationship("Product", back_populates="flash_sales")


class SocialProofActivity(Base):
    __tablename__ = "social_proof_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    user_name = Column(String(100))  # Anonymized name
    city = Column(String(100))
    activity_type = Column(String(50))  # "purchase", "viewing", "added_to_cart"
    message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="social_activities")
    product = relationship("Product")


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    referrer_reward = Column(Float, default=100.0)  # Reward for referrer
    referee_reward = Column(Float, default=100.0)  # Reward for new user
    usage_count = Column(Integer, default=0)
    max_usage = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="referral_codes")
    store = relationship("Store", back_populates="referral_codes")
    referrals = relationship("Referral", back_populates="referral_code")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id"), nullable=False)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Who shared
    referee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Who used code
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))  # First order of referee
    referrer_reward_given = Column(Boolean, default=False)
    referee_reward_given = Column(Boolean, default=False)
    referrer_reward_amount = Column(Float, default=0.0)
    referee_reward_amount = Column(Float, default=0.0)
    status = Column(String(50), default="pending")  # pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    referral_code = relationship("ReferralCode", back_populates="referrals")
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referee = relationship("User", foreign_keys=[referee_id], back_populates="referrals_used")
    store = relationship("Store")


class LoyaltyPoints(Base):
    __tablename__ = "loyalty_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    total_points = Column(Integer, default=0)
    points_earned = Column(Integer, default=0)
    points_redeemed = Column(Integer, default=0)
    tier = Column(String(20), default="bronze")  # bronze, silver, gold, platinum
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="loyalty_points")
    store = relationship("Store")
    transactions = relationship("LoyaltyTransaction", back_populates="loyalty_account")


class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loyalty_account_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_points.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    points = Column(Integer, nullable=False)  # Positive for earn, negative for redeem
    transaction_type = Column(String(50))  # "earned", "redeemed", "expired", "referral_bonus"
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    loyalty_account = relationship("LoyaltyPoints", back_populates="transactions")
