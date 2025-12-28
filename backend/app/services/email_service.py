"""
Email service for sending notifications
Supports SendGrid and SMTP
"""
import logging
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import aiosmtplib
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails via SendGrid or SMTP"""
    
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER  # 'sendgrid' or 'smtp'
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
        
        # SendGrid setup
        self.sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.sendgrid_client = None
        
        # SMTP setup
        self.smtp_host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the email provider"""
        if self.provider == 'sendgrid' and self.sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
                logger.info("SendGrid email provider initialized")
            except ImportError:
                logger.warning("SendGrid library not installed, falling back to SMTP")
                self.provider = 'smtp'
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
                self.provider = 'smtp'
        elif self.provider == 'smtp':
            logger.info(f"SMTP email provider initialized: {self.smtp_host}:{self.smtp_port}")
        else:
            logger.warning("No valid email provider configured")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send email via configured provider
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html: HTML body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            reply_to: Reply-to address (optional)
            attachments: List of attachments (optional)
        
        Returns:
            Dict with success status and message
        """
        try:
            if self.provider == 'sendgrid' and self.sendgrid_client:
                return await self._send_via_sendgrid(
                    to, subject, body, html, cc, bcc, reply_to, attachments
                )
            else:
                return await self._send_via_smtp(
                    to, subject, body, html, cc, bcc, reply_to
                )
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': self.provider
            }
    
    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        try:
            from sendgrid.helpers.mail import (
                Mail, Email, To, Cc, Bcc, Content, Attachment, 
                FileContent, FileName, FileType, Disposition
            )
            
            # Build message
            from_email = Email(self.from_email, self.from_name)
            to_email = To(to)
            
            # Create mail object
            if html:
                content = Content("text/html", html)
            else:
                content = Content("text/plain", body)
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body if not html else None,
                html_content=html if html else None
            )
            
            # Add CC
            if cc:
                message.cc = [Cc(email) for email in cc]
            
            # Add BCC
            if bcc:
                message.bcc = [Bcc(email) for email in bcc]
            
            # Add reply-to
            if reply_to:
                message.reply_to = Email(reply_to)
            
            # Add attachments
            if attachments:
                for attach in attachments:
                    attachment = Attachment()
                    attachment.file_content = FileContent(attach['content'])
                    attachment.file_name = FileName(attach['filename'])
                    attachment.file_type = FileType(attach.get('type', 'application/octet-stream'))
                    attachment.disposition = Disposition('attachment')
                    message.attachment = attachment
            
            # Send
            response = self.sendgrid_client.send(message)
            
            return {
                'success': True,
                'provider': 'sendgrid',
                'message_id': response.headers.get('X-Message-Id'),
                'status_code': response.status_code
            }
        
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            raise
    
    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            if reply_to:
                message['Reply-To'] = reply_to
            
            # Add plain text part
            part1 = MIMEText(body, 'plain')
            message.attach(part1)
            
            # Add HTML part if provided
            if html:
                part2 = MIMEText(html, 'html')
                message.attach(part2)
            
            # Build recipient list
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Send via SMTP
            if self.smtp_use_tls:
                # Use async SMTP with TLS
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    use_tls=True
                )
            else:
                # Use async SMTP without TLS
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password
                )
            
            return {
                'success': True,
                'provider': 'smtp',
                'recipients': recipients
            }
        
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render email template with variables
        
        Args:
            template: Jinja2 template string
            variables: Template variables
        
        Returns:
            Rendered template string
        """
        try:
            jinja_template = Template(template)
            return jinja_template.render(**variables)
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise
    
    async def send_templated_email(
        self,
        to: str,
        subject_template: str,
        body_template: str,
        variables: Dict[str, Any],
        html_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using templates
        
        Args:
            to: Recipient email
            subject_template: Subject template string
            body_template: Body template string
            variables: Template variables
            html_template: HTML template string (optional)
        
        Returns:
            Send result
        """
        try:
            # Render templates
            subject = self.render_template(subject_template, variables)
            body = self.render_template(body_template, variables)
            html = self.render_template(html_template, variables) if html_template else None
            
            # Send email
            return await self.send_email(to, subject, body, html)
        
        except Exception as e:
            logger.error(f"Failed to send templated email: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global email service instance
email_service = EmailService()


async def send_order_confirmation_email(
    to: str,
    order_id: str,
    customer_name: str,
    order_total: float,
    items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send order confirmation email"""
    subject = f"Order Confirmation #{order_id}"
    
    body = f"""
Hello {customer_name},

Thank you for your order! Your order #{order_id} has been confirmed.

Order Total: ${order_total:.2f}

Items:
{chr(10).join([f"- {item['name']} x{item['quantity']}: ${item['price']:.2f}" for item in items])}

We'll send you another email when your order ships.

Thank you for shopping with us!

Best regards,
{email_service.from_name}
    """.strip()
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Order Confirmation</h2>
            <p>Hello {customer_name},</p>
            <p>Thank you for your order! Your order <strong>#{order_id}</strong> has been confirmed.</p>
            
            <h3>Order Summary</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left;">Item</th>
                    <th style="padding: 8px; text-align: center;">Quantity</th>
                    <th style="padding: 8px; text-align: right;">Price</th>
                </tr>
                {''.join([f'<tr><td style="padding: 8px;">{item["name"]}</td><td style="padding: 8px; text-align: center;">{item["quantity"]}</td><td style="padding: 8px; text-align: right;">${item["price"]:.2f}</td></tr>' for item in items])}
                <tr style="border-top: 2px solid #333;">
                    <td colspan="2" style="padding: 8px; text-align: right;"><strong>Total:</strong></td>
                    <td style="padding: 8px; text-align: right;"><strong>${order_total:.2f}</strong></td>
                </tr>
            </table>
            
            <p>We'll send you another email when your order ships.</p>
            <p>Thank you for shopping with us!</p>
            
            <p>Best regards,<br>{email_service.from_name}</p>
        </body>
    </html>
    """
    
    return await email_service.send_email(to, subject, body, html)


async def send_payment_confirmation_email(
    to: str,
    order_id: str,
    customer_name: str,
    amount: float,
    payment_method: str
) -> Dict[str, Any]:
    """Send payment confirmation email"""
    subject = f"Payment Received for Order #{order_id}"
    
    body = f"""
Hello {customer_name},

We've received your payment for order #{order_id}.

Payment Details:
- Amount: ${amount:.2f}
- Method: {payment_method}

Your order is now being processed and will ship soon.

Thank you!

Best regards,
{email_service.from_name}
    """.strip()
    
    return await email_service.send_email(to, subject, body)
