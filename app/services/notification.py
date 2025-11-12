"""
Unified notification service for email and Telegram notifications.
"""
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime

from app.core.config import settings
from app.templates.email_templates import EmailTemplates

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'smtp_server', 'localhost')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', '')
        self.smtp_password = getattr(settings, 'smtp_password', '')
        self.from_email = getattr(settings, 'from_email', 'noreply@nordlayer.com')
        self.enabled = getattr(settings, 'email_notifications_enabled', False)
        
        if self.enabled:
            logger.info("Email notification service initialized")
        else:
            logger.info("Email notifications disabled")
    
    async def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email notification"""
        if not self.enabled:
            logger.debug(f"Email notifications disabled, skipping email to {to_email}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp_email, msg, to_email)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart, to_email: str):
        """Send email via SMTP (blocking operation)"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            if self.smtp_username and self.smtp_password:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg, to_addresses=[to_email])
    
    async def send_multipart_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        """Send multipart email with both text and HTML versions"""
        if not self.enabled:
            logger.debug(f"Email notifications disabled, skipping email to {to_email}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add both text and HTML parts
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp_email, msg, to_email)
            
            logger.info(f"Multipart email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send multipart email to {to_email}: {e}")
            return False
    
    async def send_order_confirmation(self, order_data: Dict[str, Any]) -> bool:
        """Send order confirmation email to customer"""
        customer_email = order_data.get('customer_email')
        if not customer_email:
            logger.warning("No customer email provided for order confirmation")
            return False
        
        subject = f"Подтверждение заказа #{order_data.get('id')} - NordLayer"
        
        # Use HTML template
        html_body = EmailTemplates.order_confirmation_html(order_data)
        text_body = EmailTemplates.order_confirmation_text(order_data)
        
        # Send HTML email with text fallback
        return await self.send_multipart_email(customer_email, subject, text_body, html_body)
    
    async def send_status_change_notification(self, order_data: Dict[str, Any]) -> bool:
        """Send status change notification email to customer"""
        customer_email = order_data.get('customer_email')
        if not customer_email:
            logger.warning("No customer email provided for status change notification")
            return False
        
        subject = f"Изменение статуса заказа #{order_data.get('id')} - NordLayer"
        
        # Use HTML template
        html_body = EmailTemplates.status_change_html(order_data)
        text_body = EmailTemplates.status_change_text(order_data)
        
        # Send HTML email with text fallback
        return await self.send_multipart_email(customer_email, subject, text_body, html_body)


class TelegramNotificationService:
    """Service for sending Telegram notifications"""
    
    def __init__(self):
        self.bot_webhook_url = getattr(settings, 'telegram_bot_webhook_url', '')
        self.admin_chat_ids = getattr(settings, 'telegram_admin_chat_ids', [])
        self.enabled = bool(self.bot_webhook_url)
        
        if self.enabled:
            logger.info("Telegram notification service initialized")
        else:
            logger.info("Telegram notifications disabled - no webhook URL configured")
    
    async def send_webhook_notification(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Send notification to Telegram bot via webhook"""
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping webhook")
            return False
        
        try:
            payload = {
                "type": notification_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.bot_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Telegram webhook notification sent: {notification_type}")
                        return True
                    else:
                        logger.error(f"Telegram webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram webhook notification: {e}")
            return False
    
    async def notify_new_order(self, order_data: Dict[str, Any]) -> bool:
        """Notify about new order via Telegram"""
        return await self.send_webhook_notification("new_order", order_data)
    
    async def notify_status_change(self, order_data: Dict[str, Any]) -> bool:
        """Notify about order status change via Telegram"""
        return await self.send_webhook_notification("status_change", order_data)


class UnifiedNotificationService:
    """Unified service that handles both email and Telegram notifications"""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.telegram_service = TelegramNotificationService()
        logger.info("Unified notification service initialized")
    
    async def notify_new_order(self, order_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send new order notifications via all channels"""
        results = {}
        
        # Send email confirmation to customer
        results['email_customer'] = await self.email_service.send_order_confirmation(order_data)
        
        # Send Telegram notification to admins
        results['telegram_admins'] = await self.telegram_service.notify_new_order(order_data)
        
        logger.info(f"New order notifications sent for order {order_data.get('id')}: {results}")
        return results
    
    async def notify_status_change(self, order_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send status change notifications via all channels"""
        results = {}
        
        # Send email to customer
        results['email_customer'] = await self.email_service.send_status_change_notification(order_data)
        
        # Send Telegram notification to customer (if order came from Telegram)
        if order_data.get('source') == 'TELEGRAM':
            results['telegram_customer'] = await self.telegram_service.notify_status_change(order_data)
        
        logger.info(f"Status change notifications sent for order {order_data.get('id')}: {results}")
        return results
    
    async def send_test_notifications(self) -> Dict[str, bool]:
        """Send test notifications to verify all services are working"""
        test_order_data = {
            'id': 'TEST',
            'customer_name': 'Test Customer',
            'customer_email': 'test@example.com',
            'service_name': 'Test Service',
            'status': 'confirmed',
            'created_at': datetime.now().isoformat()
        }
        
        results = {}
        results['email_test'] = await self.email_service.send_email(
            'test@example.com',
            'Test Email Notification - NordLayer',
            'This is a test email notification from NordLayer notification system.'
        )
        
        results['telegram_test'] = await self.telegram_service.send_webhook_notification(
            'test',
            {'message': 'Test notification from NordLayer backend'}
        )
        
        logger.info(f"Test notifications results: {results}")
        return results


# Global notification service instance
notification_service = UnifiedNotificationService()