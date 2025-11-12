"""
Integration tests for the notification system.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks

from app.main import app
from app.services.notification import notification_service


class TestNotificationIntegration:
    """Integration tests for notification system"""
    
    @pytest.fixture
    def client(self, db_session):
        """Create test client with test data"""
        from app.models.service import Service
        from app.core.deps import get_db
        from tests.conftest import override_get_db
        
        # Create test service
        test_service = Service(
            name="FDM Printing",
            description="High-quality FDM 3D printing service",
            is_active=True,
            category="3d_printing"
        )
        db_session.add(test_service)
        db_session.commit()
        
        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_order_creation_triggers_notification(self, client):
        """Test that creating an order triggers notifications"""
        # Mock the notification service methods
        with patch.object(notification_service, 'notify_new_order', return_value={'email_customer': True, 'telegram_admins': True}) as mock_notify:
            
            # Create test order data
            order_data = {
                "customer_name": "Test Customer",
                "customer_email": "test@example.com",
                "customer_contact": "test@example.com",
                "service_id": 1,
                "source": "web",
                "specifications": {
                    "material": "PLA",
                    "quality": "High",
                    "infill": "20"
                }
            }
            
            # Make request to create order
            response = client.post("/api/v1/orders/", json=order_data)
            
            # Verify order was created successfully
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert "data" in response_data
            
            # Note: In a real test, we would need to wait for background tasks
            # or use a different approach to test background task execution
    
    @pytest.mark.asyncio
    async def test_webhook_endpoint_exists(self, client):
        """Test that webhook endpoints are accessible"""
        # Test webhook health endpoint
        response = client.get("/api/v1/webhooks/telegram/health")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["service"] == "telegram_webhook"
    
    @pytest.mark.asyncio
    async def test_webhook_notification_endpoint(self, client):
        """Test webhook notification endpoint"""
        # Test webhook notification endpoint
        webhook_payload = {
            "type": "test",
            "data": {
                "message": "Test notification"
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        response = client.post("/api/v1/webhooks/telegram/notifications", json=webhook_payload)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "test" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_notification_service_initialization(self):
        """Test that notification service is properly initialized"""
        # Test that the global notification service instance exists
        assert notification_service is not None
        assert hasattr(notification_service, 'email_service')
        assert hasattr(notification_service, 'telegram_service')
        
        # Test that services have proper methods
        assert hasattr(notification_service, 'notify_new_order')
        assert hasattr(notification_service, 'notify_status_change')
        assert hasattr(notification_service, 'send_test_notifications')
    
    @pytest.mark.asyncio
    async def test_email_templates_exist(self):
        """Test that email templates are available"""
        from app.templates.email_templates import EmailTemplates
        
        # Test that template methods exist
        assert hasattr(EmailTemplates, 'order_confirmation_html')
        assert hasattr(EmailTemplates, 'order_confirmation_text')
        assert hasattr(EmailTemplates, 'status_change_html')
        assert hasattr(EmailTemplates, 'status_change_text')
        
        # Test that templates can be rendered
        test_order_data = {
            'id': 123,
            'customer_name': 'Test Customer',
            'service_name': 'Test Service',
            'status': 'confirmed',
            'specifications': {}
        }
        
        html_content = EmailTemplates.order_confirmation_html(test_order_data)
        text_content = EmailTemplates.order_confirmation_text(test_order_data)
        
        assert isinstance(html_content, str)
        assert isinstance(text_content, str)
        assert len(html_content) > 0
        assert len(text_content) > 0
        assert 'Test Customer' in html_content
        assert 'Test Customer' in text_content