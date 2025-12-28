"""
Notification schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, validator
from app.models.notification_models import NotificationType, NotificationStatus, NotificationPriority


# ==================== Template Schemas ====================

class NotificationTemplateBase(BaseModel):
    """Base template schema"""
    name: str = Field(..., min_length=1, max_length=200)
    notification_type: NotificationType
    subject: Optional[str] = Field(None, max_length=500)
    body_template: str = Field(..., min_length=1)
    sms_template: Optional[str] = None
    variables: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    """Create template request"""
    pass


class NotificationTemplateUpdate(BaseModel):
    """Update template request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=500)
    body_template: Optional[str] = Field(None, min_length=1)
    sms_template: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    """Template response"""
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Notification Schemas ====================

class NotificationBase(BaseModel):
    """Base notification schema"""
    user_id: int
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    subject: str = Field(..., max_length=500)
    body: str = Field(..., min_length=1)
    data: Dict[str, Any] = Field(default_factory=dict)


class NotificationCreate(NotificationBase):
    """Create notification request"""
    template_id: Optional[int] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    schedule_at: Optional[datetime] = None

    @validator('schedule_at')
    def validate_schedule_at(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('schedule_at must be in the future')
        return v


class NotificationBulkCreate(BaseModel):
    """Create bulk notifications"""
    user_ids: List[int] = Field(..., min_items=1)
    template_id: int
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    schedule_at: Optional[datetime] = None


class NotificationUpdate(BaseModel):
    """Update notification status"""
    status: Optional[NotificationStatus] = None
    read: Optional[bool] = None
    clicked: Optional[bool] = None


class NotificationResponse(NotificationBase):
    """Notification response"""
    id: int
    tenant_id: int
    template_id: Optional[int] = None
    status: NotificationStatus
    read: bool
    clicked: bool
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    schedule_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


# ==================== Preference Schemas ====================

class NotificationPreferenceBase(BaseModel):
    """Base preference schema"""
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    order_updates: bool = True
    payment_updates: bool = True
    shipping_updates: bool = True
    promotional: bool = True
    marketing: bool = False


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """Update preferences request"""
    pass


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Preference response"""
    id: int
    user_id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Send Notification Requests ====================

class SendEmailRequest(BaseModel):
    """Send email notification"""
    to: EmailStr
    subject: str = Field(..., max_length=500)
    body: str = Field(..., min_length=1)
    html: Optional[str] = None
    template_id: Optional[int] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[int] = None
    priority: NotificationPriority = NotificationPriority.NORMAL


class SendSMSRequest(BaseModel):
    """Send SMS notification"""
    to: str = Field(..., min_length=10, max_length=15)
    message: str = Field(..., min_length=1, max_length=1600)
    template_id: Optional[int] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[int] = None
    priority: NotificationPriority = NotificationPriority.HIGH

    @validator('to')
    def validate_phone(cls, v):
        # Remove common formatting characters
        phone = v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if not phone.isdigit():
            raise ValueError('Phone number must contain only digits')
        if len(phone) < 10 or len(phone) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return v


class SendPushRequest(BaseModel):
    """Send push notification"""
    user_id: int
    title: str = Field(..., max_length=100)
    body: str = Field(..., max_length=500)
    data: Dict[str, Any] = Field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL


class SendNotificationResponse(BaseModel):
    """Send notification response"""
    success: bool
    notification_id: Optional[int] = None
    message: str
    external_id: Optional[str] = None


# ==================== Log Schemas ====================

class NotificationLogResponse(BaseModel):
    """Notification log response"""
    id: int
    notification_id: int
    tenant_id: int
    event: str
    status: str
    message: Optional[str] = None
    meta_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Statistics ====================

class NotificationStats(BaseModel):
    """Notification statistics"""
    total_sent: int
    total_delivered: int
    total_failed: int
    total_pending: int
    delivery_rate: float
    failure_rate: float
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    recent_failures: List[NotificationResponse]


class UserNotificationStats(BaseModel):
    """User notification statistics"""
    total: int
    unread: int
    read: int
    clicked: int
    by_type: Dict[str, int]
    recent: List[NotificationResponse]
