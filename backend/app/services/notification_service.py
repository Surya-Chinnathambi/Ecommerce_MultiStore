"""
Notification service for managing all notification types
Orchestrates email, SMS, push, and in-app notifications
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.notification_models import (
    Notification,
    NotificationTemplate,
    NotificationPreference,
    NotificationLog,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)
from app.models.auth_models import User
from app.services.email_service import email_service
from app.services.sms_service import sms_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
    
    # ==================== Template Management ====================
    
    def create_template(
        self,
        name: str,
        notification_type: NotificationType,
        subject: Optional[str],
        body_template: str,
        sms_template: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> NotificationTemplate:
        """Create notification template"""
        template = NotificationTemplate(
            tenant_id=self.tenant_id,
            name=name,
            notification_type=notification_type,
            subject=subject,
            body_template=body_template,
            sms_template=sms_template,
            variables=variables or {}
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created notification template: {name}")
        return template
    
    def get_template(self, template_id: int) -> Optional[NotificationTemplate]:
        """Get template by ID"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id,
            NotificationTemplate.tenant_id == self.tenant_id
        ).first()
    
    def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get template by name"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.name == name,
            NotificationTemplate.tenant_id == self.tenant_id
        ).first()
    
    def list_templates(
        self,
        notification_type: Optional[NotificationType] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationTemplate]:
        """List templates"""
        query = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.tenant_id == self.tenant_id
        )
        
        if notification_type:
            query = query.filter(NotificationTemplate.notification_type == notification_type)
        
        if is_active is not None:
            query = query.filter(NotificationTemplate.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def update_template(
        self,
        template_id: int,
        **kwargs
    ) -> Optional[NotificationTemplate]:
        """Update template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    # ==================== User Preferences ====================
    
    def get_user_preferences(self, user_id: int) -> NotificationPreference:
        """Get user notification preferences"""
        prefs = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.tenant_id == self.tenant_id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(
                user_id=user_id,
                tenant_id=self.tenant_id
            )
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)
        
        return prefs
    
    def update_user_preferences(
        self,
        user_id: int,
        **kwargs
    ) -> NotificationPreference:
        """Update user preferences"""
        prefs = self.get_user_preferences(user_id)
        
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        self.db.commit()
        self.db.refresh(prefs)
        
        return prefs
    
    # ==================== Notification Creation ====================
    
    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        subject: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        template_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        schedule_at: Optional[datetime] = None
    ) -> Notification:
        """Create notification"""
        notification = Notification(
            tenant_id=self.tenant_id,
            user_id=user_id,
            template_id=template_id,
            notification_type=notification_type,
            priority=priority,
            subject=subject,
            body=body,
            data=data or {},
            schedule_at=schedule_at,
            status=NotificationStatus.PENDING if schedule_at else NotificationStatus.PENDING
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # If not scheduled, send immediately
        if not schedule_at:
            await self.send_notification(notification.id)
        
        return notification
    
    async def create_from_template(
        self,
        user_id: int,
        template_name: str,
        variables: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        schedule_at: Optional[datetime] = None
    ) -> Optional[Notification]:
        """Create notification from template"""
        template = self.get_template_by_name(template_name)
        if not template or not template.is_active:
            logger.error(f"Template not found or inactive: {template_name}")
            return None
        
        # Render templates
        try:
            subject = email_service.render_template(template.subject, variables) if template.subject else ""
            body = email_service.render_template(template.body_template, variables)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return None
        
        return await self.create_notification(
            user_id=user_id,
            notification_type=template.notification_type,
            subject=subject,
            body=body,
            data=variables,
            template_id=template.id,
            priority=priority,
            schedule_at=schedule_at
        )
    
    async def create_bulk_notifications(
        self,
        user_ids: List[int],
        template_name: str,
        variables: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> List[Notification]:
        """Create bulk notifications from template"""
        notifications = []
        
        for user_id in user_ids:
            notification = await self.create_from_template(
                user_id=user_id,
                template_name=template_name,
                variables=variables,
                priority=priority
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    # ==================== Notification Sending ====================
    
    async def send_notification(self, notification_id: int) -> bool:
        """Send notification via appropriate channel"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if not notification:
            logger.error(f"Notification not found: {notification_id}")
            return False
        
        # Check if already sent
        if notification.status == NotificationStatus.SENT:
            logger.info(f"Notification already sent: {notification_id}")
            return True
        
        # Get user preferences
        prefs = self.get_user_preferences(notification.user_id)
        
        # Get user info
        user = self.db.query(User).filter(User.id == notification.user_id).first()
        if not user:
            self._log_notification_event(notification_id, "error", "failed", "User not found")
            self._update_notification_status(notification_id, NotificationStatus.FAILED, "User not found")
            return False
        
        try:
            # Send via appropriate channel based on type and preferences
            if notification.notification_type == NotificationType.EMAIL and prefs.email_enabled:
                result = await self._send_email_notification(notification, user)
            elif notification.notification_type == NotificationType.SMS and prefs.sms_enabled:
                result = await self._send_sms_notification(notification, user)
            elif notification.notification_type == NotificationType.PUSH and prefs.push_enabled:
                result = await self._send_push_notification(notification, user)
            elif notification.notification_type == NotificationType.IN_APP and prefs.in_app_enabled:
                result = await self._send_in_app_notification(notification, user)
            else:
                logger.info(f"Notification type disabled by user: {notification.notification_type}")
                self._update_notification_status(notification_id, NotificationStatus.SKIPPED, "Disabled by user")
                return False
            
            if result['success']:
                self._update_notification_status(notification_id, NotificationStatus.SENT)
                self._log_notification_event(notification_id, "sent", "success", "Notification sent successfully")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                self._update_notification_status(notification_id, NotificationStatus.FAILED, error_msg)
                self._log_notification_event(notification_id, "error", "failed", error_msg)
                
                # Retry logic
                if notification.retry_count < 3:
                    notification.retry_count += 1
                    self.db.commit()
                    logger.info(f"Will retry notification {notification_id} (attempt {notification.retry_count})")
                
                return False
        
        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {e}")
            self._update_notification_status(notification_id, NotificationStatus.FAILED, str(e))
            self._log_notification_event(notification_id, "error", "failed", str(e))
            return False
    
    async def _send_email_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send email notification"""
        if not user.email:
            return {'success': False, 'error': 'User has no email'}
        
        return await email_service.send_email(
            to=user.email,
            subject=notification.subject,
            body=notification.body
        )
    
    async def _send_sms_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send SMS notification"""
        if not user.phone:
            return {'success': False, 'error': 'User has no phone'}
        
        # Use SMS template if available
        template = notification.template
        message = notification.body
        
        if template and template.sms_template:
            try:
                message = sms_service.render_template(template.sms_template, notification.data)
            except Exception as e:
                logger.error(f"Failed to render SMS template: {e}")
        
        return await sms_service.send_sms(
            to=user.phone,
            message=message
        )
    
    async def _send_push_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send push notification"""
        # TODO: Implement push notification via Firebase/OneSignal
        logger.info(f"Push notification to user {user.id}: {notification.subject}")
        return {'success': True, 'provider': 'push', 'message': 'Push not implemented yet'}
    
    async def _send_in_app_notification(self, notification: Notification, user: User) -> Dict[str, Any]:
        """Send in-app notification"""
        # In-app notifications are just database records
        # The frontend will poll/subscribe to get them
        return {'success': True, 'provider': 'in_app'}
    
    # ==================== Notification Management ====================
    
    def get_notification(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.tenant_id == self.tenant_id
        ).first()
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Notification], int]:
        """Get user notifications"""
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.tenant_id == self.tenant_id
        )
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        
        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        
        return notifications, total
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.tenant_id == self.tenant_id
        ).first()
        
        if not notification:
            return False
        
        notification.read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        
        self._log_notification_event(notification_id, "read", "success", "Notification read")
        return True
    
    def mark_as_clicked(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as clicked"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.tenant_id == self.tenant_id
        ).first()
        
        if not notification:
            return False
        
        notification.clicked = True
        notification.clicked_at = datetime.utcnow()
        
        if not notification.read:
            notification.read = True
            notification.read_at = datetime.utcnow()
        
        self.db.commit()
        
        self._log_notification_event(notification_id, "clicked", "success", "Notification clicked")
        return True
    
    def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count"""
        return self.db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.tenant_id == self.tenant_id,
            Notification.read == False
        ).scalar()
    
    # ==================== Statistics ====================
    
    def get_notification_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get notification statistics"""
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Total stats
        total = self.db.query(func.count(Notification.id)).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.created_at >= since
        ).scalar()
        
        sent = self.db.query(func.count(Notification.id)).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.status == NotificationStatus.SENT,
            Notification.created_at >= since
        ).scalar()
        
        failed = self.db.query(func.count(Notification.id)).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.status == NotificationStatus.FAILED,
            Notification.created_at >= since
        ).scalar()
        
        pending = self.db.query(func.count(Notification.id)).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.status == NotificationStatus.PENDING,
            Notification.created_at >= since
        ).scalar()
        
        # By type
        by_type = {}
        for ntype in NotificationType:
            count = self.db.query(func.count(Notification.id)).filter(
                Notification.tenant_id == self.tenant_id,
                Notification.notification_type == ntype,
                Notification.created_at >= since
            ).scalar()
            by_type[ntype.value] = count
        
        # Recent failures
        recent_failures = self.db.query(Notification).filter(
            Notification.tenant_id == self.tenant_id,
            Notification.status == NotificationStatus.FAILED
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        return {
            'total_sent': sent,
            'total_failed': failed,
            'total_pending': pending,
            'delivery_rate': (sent / total * 100) if total > 0 else 0,
            'failure_rate': (failed / total * 100) if total > 0 else 0,
            'by_type': by_type,
            'recent_failures': recent_failures
        }
    
    # ==================== Helper Methods ====================
    
    def _update_notification_status(
        self,
        notification_id: int,
        status: NotificationStatus,
        error_message: Optional[str] = None
    ):
        """Update notification status"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if notification:
            notification.status = status
            
            if status == NotificationStatus.SENT:
                notification.sent_at = datetime.utcnow()
            elif status == NotificationStatus.FAILED:
                notification.failed_at = datetime.utcnow()
                notification.error_message = error_message
            
            self.db.commit()
    
    def _log_notification_event(
        self,
        notification_id: int,
        event: str,
        status: str,
        message: Optional[str] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ):
        """Log notification event"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if notification:
            log = NotificationLog(
                notification_id=notification_id,
                tenant_id=notification.tenant_id,
                event=event,
                status=status,
                message=message,
                meta_data=meta_data or {}
            )
            
            self.db.add(log)
            self.db.commit()


def get_notification_service(db: Session, tenant_id: int) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(db, tenant_id)
