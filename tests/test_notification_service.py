"""
Tests for the notification service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.notification import (
    EmailNotificationService,
    TelegramNotificationService,
    UnifiedNotificationService
)


class TestEmailNotificationService:
    """Tests for EmailNotificationService"""
    
    @pytest.fixture
    def email_service(self):
        """Create email service instance for testing"""
        with patch('app.services.notification.settings') as mock_settings:
            mock_settings.email_notifications_enabled = True
            mock_settings.smtp_server = 'localhost'
            mock_settings.smtp_port = 587
            mock_settings.smtp_username = 'test@example.com'
            mock_settings.smtp_password = 'password'
            mock_settings.from_email = 'noreply@nordlayer.com'
            return EmailNotificationService()
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing"""
        return {
            'id': 123,
            'customer_name': 'Test Customer',
            'customer_email': 'customer@example.com',
            'service_name': 'FDM Printing',
            'status': 'confirmed',
            'created_at': '2024-01-01T12:00:00',
            'specifications': {
                'material': 'PLA',
                'quality': 'High',
                'infill': '20',
                'files_info': [{'name': 'model.stl', 'size': 1024}]
            }
        }
    
    @pytest.mark.asyncio
    async def test_send_email_disabled(self):
        """Test email sending when disabled"""
        with patch('app.services.notification.settings') as mock_settings:
            mock_settings.email_notifications_enabled = False
            service = EmailNotificationService()
            
            result = await service.send_email(
                'test@example.com',
                'Test Subject',
                'Test Body'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_order_confirmation(self, email_service, sample_order_data):
        """Test sending order confirmation email"""
        with patch.object(email_service, 'send_multipart_email', return_value=True) as mock_send:
            result = await email_service.send_order_confirmation(sample_order_data)
            
            assert result is True
            mock_send.assert_called_once()
            
            # Check call arguments
            args, kwargs = mock_send.call_args
            assert args[0] == 'customer@example.com'  # to_email
            assert 'Подтверждение заказа #123' in args[1]  # subject
            assert 'Test Customer' in args[2]  # text_body
            assert 'Test Customer' in args[3]  # html_body
    
    @pytest.mark.asyncio
    async def test_send_order_confirmation_no_email(self, email_service):
        """Test sending order confirmation without customer email"""
        order_data = {'id': 123, 'customer_name': 'Test Customer'}
        
        result = await email_service.send_order_confirmation(order_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_status_change_notification(self, email_service, sample_order_data):
        """Test sending status change notification"""
        sample_order_data['status'] = 'ready'
        
        with patch.object(email_service, 'send_multipart_email', return_value=True) as mock_send:
            result = await email_service.send_status_change_notification(sample_order_data)
            
            assert result is True
            mock_send.assert_called_once()
            
            # Check call arguments
            args, kwargs = mock_send.call_args
            assert args[0] == 'customer@example.com'  # to_email
            assert 'Изменение статуса заказа #123' in args[1]  # subject


class TestTelegramNotificationService:
    """Tests for TelegramNotificationService"""
    
    @pytest.fixture
    def telegram_service(self):
        """Create telegram service instance for testing"""
        with patch('app.services.notification.settings') as mock_settings:
            mock_settings.telegram_bot_webhook_url = 'http://localhost:8081/webhook/notifications'
            mock_settings.telegram_admin_chat_ids = [123456, 789012]
            return TelegramNotificationService()
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing"""
        return {
            'id': 123,
            'customer_name': 'Test Customer',
            'customer_email': 'customer@example.com',
            'service_name': 'FDM Printing',
            'status': 'confirmed',
            'source': 'TELEGRAM'
        }
    
    @pytest.mark.asyncio
    async def test_send_webhook_notification_disabled(self):
        """Test webhook notification when disabled"""
        with patch('app.services.notification.settings') as mock_settings:
            mock_settings.telegram_bot_webhook_url = ''
            service = TelegramNotificationService()
            
            result = await service.send_webhook_notification('test', {})
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_notify_new_order(self, telegram_service, sample_order_data):
        """Test new order notification"""
        with patch.object(telegram_service, 'send_webhook_notification', return_value=True) as mock_webhook:
            result = await telegram_service.notify_new_order(sample_order_data)
            
            assert result is True
            mock_webhook.assert_called_once_with('new_order', sample_order_data)
    
    @pytest.mark.asyncio
    async def test_notify_status_change(self, telegram_service, sample_order_data):
        """Test status change notification"""
        with patch.object(telegram_service, 'send_webhook_notification', return_value=True) as mock_webhook:
            result = await telegram_service.notify_status_change(sample_order_data)
            
            assert result is True
            mock_webhook.assert_called_once_with('status_change', sample_order_data)
    
    @pytest.mark.asyncio
    async def test_send_webhook_notification_success(self, telegram_service):
        """Test successful webhook notification"""
        with patch.object(telegram_service, 'send_webhook_notification', return_value=True) as mock_send:
            result = await telegram_service.send_webhook_notification('test', {'message': 'test'})
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_send_webhook_notification_failure(self, telegram_service):
        """Test failed webhook notification"""
        with patch.object(telegram_service, 'send_webhook_notification', return_value=False) as mock_send:
            result = await telegram_service.send_webhook_notification('test', {'message': 'test'})
            
            assert result is False


class TestUnifiedNotificationService:
    """Tests for UnifiedNotificationService"""
    
    @pytest.fixture
    def unified_service(self):
        """Create unified service instance for testing"""
        return UnifiedNotificationService()
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing"""
        return {
            'id': 123,
            'customer_name': 'Test Customer',
            'customer_email': 'customer@example.com',
            'service_name': 'FDM Printing',
            'status': 'confirmed',
            'source': 'WEB'
        }
    
    @pytest.mark.asyncio
    async def test_notify_new_order(self, unified_service, sample_order_data):
        """Test unified new order notification"""
        with patch.object(unified_service.email_service, 'send_order_confirmation', return_value=True) as mock_email, \
             patch.object(unified_service.telegram_service, 'notify_new_order', return_value=True) as mock_telegram:
            
            results = await unified_service.notify_new_order(sample_order_data)
            
            assert results['email_customer'] is True
            assert results['telegram_admins'] is True
            
            mock_email.assert_called_once_with(sample_order_data)
            mock_telegram.assert_called_once_with(sample_order_data)
    
    @pytest.mark.asyncio
    async def test_notify_status_change_web_order(self, unified_service, sample_order_data):
        """Test status change notification for web order"""
        with patch.object(unified_service.email_service, 'send_status_change_notification', return_value=True) as mock_email:
            
            results = await unified_service.notify_status_change(sample_order_data)
            
            assert results['email_customer'] is True
            assert 'telegram_customer' not in results  # Should not send Telegram for web orders
            
            mock_email.assert_called_once_with(sample_order_data)
    
    @pytest.mark.asyncio
    async def test_notify_status_change_telegram_order(self, unified_service, sample_order_data):
        """Test status change notification for Telegram order"""
        sample_order_data['source'] = 'TELEGRAM'
        
        with patch.object(unified_service.email_service, 'send_status_change_notification', return_value=True) as mock_email, \
             patch.object(unified_service.telegram_service, 'notify_status_change', return_value=True) as mock_telegram:
            
            results = await unified_service.notify_status_change(sample_order_data)
            
            assert results['email_customer'] is True
            assert results['telegram_customer'] is True
            
            mock_email.assert_called_once_with(sample_order_data)
            mock_telegram.assert_called_once_with(sample_order_data)
    
    @pytest.mark.asyncio
    async def test_send_test_notifications(self, unified_service):
        """Test sending test notifications"""
        with patch.object(unified_service.email_service, 'send_email', return_value=True) as mock_email, \
             patch.object(unified_service.telegram_service, 'send_webhook_notification', return_value=True) as mock_telegram:
            
            results = await unified_service.send_test_notifications()
            
            assert results['email_test'] is True
            assert results['telegram_test'] is True
            
            mock_email.assert_called_once()
            mock_telegram.assert_called_once()


# Integration tests
class TestNotificationIntegration:
    """Integration tests for notification system"""
    
    @pytest.mark.asyncio
    async def test_email_template_rendering(self):
        """Test that email templates render correctly"""
        from app.templates.email_templates import EmailTemplates
        
        order_data = {
            'id': 123,
            'customer_name': 'Test Customer',
            'service_name': 'FDM Printing',
            'status': 'confirmed',
            'specifications': {
                'material': 'PLA',
                'quality': 'High',
                'infill': '20',
                'files_info': [{'name': 'model.stl'}]
            }
        }
        
        # Test HTML template
        html_content = EmailTemplates.order_confirmation_html(order_data)
        assert 'Test Customer' in html_content
        assert '#123' in html_content
        assert 'FDM Printing' in html_content
        assert 'PLA' in html_content
        
        # Test text template
        text_content = EmailTemplates.order_confirmation_text(order_data)
        assert 'Test Customer' in text_content
        assert '#123' in text_content
        assert 'FDM Printing' in text_content
        assert 'PLA' in text_content
    
    @pytest.mark.asyncio
    async def test_status_change_template_rendering(self):
        """Test status change template rendering"""
        from app.templates.email_templates import EmailTemplates
        
        order_data = {
            'id': 456,
            'customer_name': 'Another Customer',
            'service_name': 'SLA Printing',
            'status': 'ready'
        }
        
        # Test HTML template
        html_content = EmailTemplates.status_change_html(order_data)
        assert 'Another Customer' in html_content
        assert '#456' in html_content
        assert 'ГОТОВ К ПОЛУЧЕНИЮ' in html_content
        
        # Test text template
        text_content = EmailTemplates.status_change_text(order_data)
        assert 'Another Customer' in text_content
        assert '#456' in text_content
        assert 'ГОТОВ К ПОЛУЧЕНИЮ' in text_content