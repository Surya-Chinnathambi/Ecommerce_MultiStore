"""
Product Review and Rating Models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class ProductReview(Base):
    """Product reviews and ratings"""
    __tablename__ = "product_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), index=True)  # For verified purchases
    
    # Rating & Review
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200))
    review_text = Column(Text)
    
    # Images
    images = Column(Text)  # JSON array of image URLs
    
    # Status
    is_verified_purchase = Column(Boolean, default=False, index=True)
    is_approved = Column(Boolean, default=True, index=True)  # For moderation
    is_featured = Column(Boolean, default=False, index=True)
    
    # Helpfulness
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    store = relationship("Store")
    user = relationship("User", back_populates="reviews")
    order = relationship("Order")
    responses = relationship("ReviewResponse", back_populates="review", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_rating', 'product_id', 'rating'),
        Index('idx_store_approved', 'store_id', 'is_approved'),
        Index('idx_user_verified', 'user_id', 'is_verified_purchase'),
    )


class ReviewResponse(Base):
    """Store/Admin responses to reviews"""
    __tablename__ = "review_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("product_reviews.id"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    responder_name = Column(String(200), nullable=False)  # Store owner/admin name
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    review = relationship("ProductReview", back_populates="responses")
    store = relationship("Store")


class ReviewHelpful(Base):
    """Track which users found reviews helpful"""
    __tablename__ = "review_helpful"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("product_reviews.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    is_helpful = Column(Boolean, nullable=False)  # True = helpful, False = not helpful
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_review_user_helpful', 'review_id', 'user_id', unique=True),
    )
