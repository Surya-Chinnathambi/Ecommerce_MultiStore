"""
SMS service for sending notifications
Supports Twilio and MSG91
"""
import logging
from typing import Optional, Dict, Any
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for sending text messages"""
    
    def __init__(self):
        self.provider = getattr(settings, 'SMS_PROVIDER', 'twilio')  # 'twilio' or 'msg91'
        self.from_number = getattr(settings, 'SMS_FROM_NUMBER', None)
        
        # Twilio setup
        self.twilio_account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.twilio_client = None
        
        # MSG91 setup
        self.msg91_auth_key = getattr(settings, 'MSG91_AUTH_KEY', None)
        self.msg91_sender_id = getattr(settings, 'MSG91_SENDER_ID', None)
        
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the SMS provider"""
        if self.provider == 'twilio' and self.twilio_account_sid and self.twilio_auth_token:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio SMS provider initialized")
            except ImportError:
                logger.error("Twilio library not installed. Install with: pip install twilio")
                self.provider = None
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
                self.provider = None
        elif self.provider == 'msg91' and self.msg91_auth_key:
            logger.info("MSG91 SMS provider initialized")
        else:
            logger.warning("No valid SMS provider configured")
            self.provider = None
    
    async def send_sms(
        self,
        to: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send SMS via configured provider
        
        Args:
            to: Recipient phone number (E.164 format recommended)
            message: SMS message text (max 1600 chars)
            metadata: Additional metadata
        
        Returns:
            Dict with success status and message
        """
        if not self.provider:
            return {
                'success': False,
                'error': 'No SMS provider configured',
                'provider': None
            }
        
        # Validate message length
        if len(message) > 1600:
            return {
                'success': False,
                'error': 'Message too long (max 1600 characters)',
                'provider': self.provider
            }
        
        try:
            if self.provider == 'twilio':
                return await self._send_via_twilio(to, message, metadata)
            elif self.provider == 'msg91':
                return await self._send_via_msg91(to, message, metadata)
            else:
                return {
                    'success': False,
                    'error': 'Invalid SMS provider',
                    'provider': self.provider
                }
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': self.provider
            }
    
    async def _send_via_twilio(
        self,
        to: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            # Normalize phone number
            if not to.startswith('+'):
                # Assume US number if no country code
                to = f"+1{to}"
            
            # Send message
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            return {
                'success': True,
                'provider': 'twilio',
                'message_sid': message_obj.sid,
                'status': message_obj.status,
                'to': to,
                'segments': message_obj.num_segments
            }
        
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            raise
    
    async def _send_via_msg91(
        self,
        to: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS via MSG91"""
        try:
            import httpx
            
            # MSG91 API endpoint
            url = "https://api.msg91.com/api/v5/flow/"
            
            # Prepare request
            headers = {
                'authkey': self.msg91_auth_key,
                'content-type': 'application/json'
            }
            
            # Remove country code prefix for India numbers
            phone = to.replace('+91', '').replace('+', '')
            
            payload = {
                'sender': self.msg91_sender_id,
                'mobiles': phone,
                'message': message
            }
            
            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
            
            return {
                'success': True,
                'provider': 'msg91',
                'message_id': result.get('message_id'),
                'response': result,
                'to': to
            }
        
        except Exception as e:
            logger.error(f"MSG91 error: {e}")
            raise
    
    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render SMS template with variables
        
        Args:
            template: Jinja2 template string
            variables: Template variables
        
        Returns:
            Rendered template string
        """
        try:
            jinja_template = Template(template)
            rendered = jinja_template.render(**variables)
            
            # Ensure it fits in SMS length
            if len(rendered) > 1600:
                logger.warning(f"Rendered SMS template exceeds 1600 chars: {len(rendered)}")
            
            return rendered
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise
    
    async def send_templated_sms(
        self,
        to: str,
        template: str,
        variables: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send SMS using template
        
        Args:
            to: Recipient phone number
            template: SMS template string
            variables: Template variables
            metadata: Additional metadata
        
        Returns:
            Send result
        """
        try:
            # Render template
            message = self.render_template(template, variables)
            
            # Send SMS
            return await self.send_sms(to, message, metadata)
        
        except Exception as e:
            logger.error(f"Failed to send templated SMS: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_otp(
        self,
        to: str,
        otp: str,
        expiry_minutes: int = 10
    ) -> Dict[str, Any]:
        """Send OTP SMS"""
        message = f"Your OTP is {otp}. Valid for {expiry_minutes} minutes. Do not share with anyone."
        return await self.send_sms(to, message)
    
    async def send_order_update(
        self,
        to: str,
        order_id: str,
        status: str,
        tracking_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send order update SMS"""
        if tracking_number:
            message = f"Order #{order_id} {status}. Track: {tracking_number}"
        else:
            message = f"Order #{order_id} {status}."
        
        return await self.send_sms(to, message)


# Global SMS service instance
sms_service = SMSService()


async def send_order_confirmation_sms(
    to: str,
    order_id: str,
    customer_name: str,
    total: float
) -> Dict[str, Any]:
    """Send order confirmation SMS"""
    message = f"Hi {customer_name}, your order #{order_id} (${total:.2f}) is confirmed! Thank you for shopping with us."
    return await sms_service.send_sms(to, message)


async def send_payment_confirmation_sms(
    to: str,
    order_id: str,
    amount: float
) -> Dict[str, Any]:
    """Send payment confirmation SMS"""
    message = f"Payment of ${amount:.2f} received for order #{order_id}. Your order is being processed."
    return await sms_service.send_sms(to, message)


async def send_shipping_notification_sms(
    to: str,
    order_id: str,
    tracking_number: str,
    carrier: str
) -> Dict[str, Any]:
    """Send shipping notification SMS"""
    message = f"Order #{order_id} shipped via {carrier}. Track: {tracking_number}"
    return await sms_service.send_sms(to, message)


async def send_delivery_notification_sms(
    to: str,
    order_id: str
) -> Dict[str, Any]:
    """Send delivery notification SMS"""
    message = f"Order #{order_id} delivered! Hope you love it. Please rate your experience."
    return await sms_service.send_sms(to, message)
