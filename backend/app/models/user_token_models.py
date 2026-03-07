from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class UserRefreshToken(Base):
    """
    Stored refresh tokens to support rotation and multi-device sessions.
    When a refresh token is used, it is rotated (new token issued, old revoked).
    """
    __tablename__ = "user_refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # The actual token JTI (unique identifier from JWT)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    
    # Metadata for session management
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(100), nullable=True)
    
    # Lifecycle
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Rotation support
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by = Column(String(255), nullable=True) # JTI of the token that replaced this one

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<UserRefreshToken {self.jti[:8]} user={self.user_id}>"
