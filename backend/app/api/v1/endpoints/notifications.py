"""
Notification API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User
from app.models.notification_models import NotificationType, NotificationPriority
from app.schemas.notification_schemas import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    NotificationCreate,
    NotificationBulkCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    SendEmailRequest,
    SendSMSRequest,
    SendPushRequest,
    SendNotificationResponse,
    NotificationStats,
    UserNotificationStats
)
from app.services.notification_service import get_notification_service
from app.services.email_service import email_service
from app.services.sms_service import sms_service

router = APIRouter()


# ==================== Template Endpoints ====================

@router.post("/templates", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create notification template (Admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    return service.create_template(
        name=template.name,
        notification_type=template.notification_type,
        subject=template.subject,
        body_template=template.body_template,
        sms_template=template.sms_template,
        variables=template.variables
    )


@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def list_templates(
    notification_type: Optional[NotificationType] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List notification templates"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    return service.list_templates(notification_type, is_active, skip, limit)


@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template by ID"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    template = service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.patch("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def update_template(
    template_id: int,
    updates: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update template"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    template = service.update_template(template_id, **updates.dict(exclude_unset=True))
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


# ==================== Notification Endpoints ====================

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create notification"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    
    # If template specified, use template
    if notification.template_id:
        return await service.create_from_template(
            user_id=notification.user_id,
            template_name="",  # Will be fetched by ID
            variables=notification.template_variables,
            priority=notification.priority,
            schedule_at=notification.schedule_at
        )
    else:
        return await service.create_notification(
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            subject=notification.subject,
            body=notification.body,
            data=notification.data,
            priority=notification.priority,
            schedule_at=notification.schedule_at
        )


@router.post("/bulk", response_model=List[NotificationResponse])
async def create_bulk_notifications(
    bulk: NotificationBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create bulk notifications"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    
    # Get template name
    template = service.get_template(bulk.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return await service.create_bulk_notifications(
        user_ids=bulk.user_ids,
        template_name=template.name,
        variables=bulk.template_variables,
        priority=bulk.priority
    )


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = False,
    notification_type: Optional[NotificationType] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user notifications"""
    service = get_notification_service(db, current_user.store_id)
    notifications, total = service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        notification_type=notification_type,
        skip=skip,
        limit=limit
    )
    
    unread_count = service.get_unread_count(current_user.id)
    
    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count"""
    service = get_notification_service(db, current_user.store_id)
    count = service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification by ID"""
    service = get_notification_service(db, current_user.store_id)
    notification = service.get_notification(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if notification.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return notification


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    updates: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification"""
    service = get_notification_service(db, current_user.store_id)
    notification = service.get_notification(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    if updates.read is not None and updates.read:
        service.mark_as_read(notification_id, current_user.id)
    
    if updates.clicked is not None and updates.clicked:
        service.mark_as_clicked(notification_id, current_user.id)
    
    # Refresh and return
    db.refresh(notification)
    return notification


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    service = get_notification_service(db, current_user.store_id)
    success = service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    service = get_notification_service(db, current_user.store_id)
    notifications, _ = service.get_user_notifications(
        user_id=current_user.id,
        unread_only=True,
        limit=1000
    )
    
    for notification in notifications:
        service.mark_as_read(notification.id, current_user.id)
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


# ==================== Preferences ====================

@router.get("/preferences/me", response_model=NotificationPreferenceResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's notification preferences"""
    service = get_notification_service(db, current_user.store_id)
    return service.get_user_preferences(current_user.id)


@router.put("/preferences/me", response_model=NotificationPreferenceResponse)
async def update_my_preferences(
    preferences: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's notification preferences"""
    service = get_notification_service(db, current_user.store_id)
    return service.update_user_preferences(
        user_id=current_user.id,
        **preferences.dict()
    )


# ==================== Send Endpoints ====================

@router.post("/send/email", response_model=SendNotificationResponse)
async def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send email notification"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If template specified, render it
    if request.template_id:
        service = get_notification_service(db, current_user.store_id)
        template = service.get_template(request.template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        subject = email_service.render_template(template.subject, request.template_variables)
        body = email_service.render_template(template.body_template, request.template_variables)
        html = request.html
    else:
        subject = request.subject
        body = request.body
        html = request.html
    
    # Send email
    result = await email_service.send_email(request.to, subject, body, html)
    
    # Create notification record if user_id provided
    if request.user_id:
        service = get_notification_service(db, current_user.store_id)
        notification = await service.create_notification(
            user_id=request.user_id,
            notification_type=NotificationType.EMAIL,
            subject=subject,
            body=body,
            priority=request.priority
        )
        
        return SendNotificationResponse(
            success=result.get('success', False),
            notification_id=notification.id,
            message="Email sent successfully" if result.get('success') else result.get('error', 'Failed to send'),
            external_id=result.get('message_id')
        )
    
    return SendNotificationResponse(
        success=result.get('success', False),
        message="Email sent successfully" if result.get('success') else result.get('error', 'Failed to send'),
        external_id=result.get('message_id')
    )


@router.post("/send/sms", response_model=SendNotificationResponse)
async def send_sms(
    request: SendSMSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send SMS notification"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If template specified, render it
    if request.template_id:
        service = get_notification_service(db, current_user.store_id)
        template = service.get_template(request.template_id)
        
        if not template or not template.sms_template:
            raise HTTPException(status_code=404, detail="SMS template not found")
        
        message = sms_service.render_template(template.sms_template, request.template_variables)
    else:
        message = request.message
    
    # Send SMS
    result = await sms_service.send_sms(request.to, message)
    
    # Create notification record if user_id provided
    if request.user_id:
        service = get_notification_service(db, current_user.store_id)
        notification = await service.create_notification(
            user_id=request.user_id,
            notification_type=NotificationType.SMS,
            subject="SMS Notification",
            body=message,
            priority=request.priority
        )
        
        return SendNotificationResponse(
            success=result.get('success', False),
            notification_id=notification.id,
            message="SMS sent successfully" if result.get('success') else result.get('error', 'Failed to send'),
            external_id=result.get('message_sid')
        )
    
    return SendNotificationResponse(
        success=result.get('success', False),
        message="SMS sent successfully" if result.get('success') else result.get('error', 'Failed to send'),
        external_id=result.get('message_sid')
    )


@router.post("/send/push", response_model=SendNotificationResponse)
async def send_push(
    request: SendPushRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send push notification"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    notification = await service.create_notification(
        user_id=request.user_id,
        notification_type=NotificationType.PUSH,
        subject=request.title,
        body=request.body,
        data=request.data,
        priority=request.priority
    )
    
    return SendNotificationResponse(
        success=True,
        notification_id=notification.id,
        message="Push notification created"
    )


# ==================== Statistics ====================

@router.get("/stats/all", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics (Admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_notification_service(db, current_user.store_id)
    return service.get_notification_stats(days)
