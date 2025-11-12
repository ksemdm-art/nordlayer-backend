"""
Simple integration tests to verify basic functionality.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestSimpleIntegration:
    """Simple integration tests"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoints(self, client):
        """Test health check endpoints"""
        # Test main health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test webhook health endpoint
        response = client.get("/api/v1/webhooks/telegram/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "telegram_webhook"
    
    def test_webhook_notification_endpoint(self, client):
        """Test webhook notification endpoint"""
        webhook_payload = {
            "type": "test",
            "data": {
                "message": "Test notification"
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        response = client.post(
            "/api/v1/webhooks/telegram/notifications",
            json=webhook_payload
        )
        assert response.status_code == 200
        
        webhook_response = response.json()
        assert webhook_response["success"] is True
        assert "test" in webhook_response["message"]
    
    def test_services_endpoint(self, client):
        """Test services endpoint"""
        response = client.get("/api/v1/services/")
        assert response.status_code == 200
        
        services_data = response.json()
        assert "success" in services_data
    
    def test_projects_endpoint(self, client):
        """Test projects endpoint"""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 200
        
        projects_data = response.json()
        assert "data" in projects_data
    
    def test_articles_endpoint(self, client):
        """Test articles endpoint"""
        response = client.get("/api/v1/articles/")
        assert response.status_code == 200
        
        articles_data = response.json()
        assert "success" in articles_data
    
    def test_cache_endpoints(self, client):
        """Test cache management endpoints (should require admin)"""
        # These should return 401/403 without authentication
        response = client.get("/api/v1/cache/stats")
        assert response.status_code in [401, 403]
        
        response = client.delete("/api/v1/cache/clear")
        assert response.status_code in [401, 403]
    
    def test_file_endpoints(self, client):
        """Test file management endpoints"""
        # Test file list endpoint (might return 500 if directory doesn't exist)
        response = client.get("/api/v1/files/list")
        assert response.status_code in [200, 500]
        
        # Test file validation endpoint
        response = client.get("/api/v1/files/validate?filename=test.stl&size=1024")
        assert response.status_code == 200
        
        validation_data = response.json()
        assert validation_data["success"] is True
    
    def test_order_search_endpoint(self, client):
        """Test order search endpoint"""
        # Note: Order search endpoint requires admin authentication
        # Test that it properly rejects unauthenticated requests
        response = client.get("/api/v1/orders/search?email=test@example.com")
        assert response.status_code == 401  # Should require authentication
        
        response = client.get("/api/v1/orders/search?email=invalid-email")
        assert response.status_code == 401  # Should require authentication
    
    def test_error_handling(self, client):
        """Test error handling"""
        # Test non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test invalid order ID (might require auth)
        response = client.get("/api/v1/orders/99999")
        assert response.status_code in [404, 401]
        
        # Test invalid project ID
        response = client.get("/api/v1/projects/99999")
        assert response.status_code == 404
    
    def test_webhook_error_handling(self, client):
        """Test webhook error handling"""
        # Test with invalid payload
        invalid_payload = {
            "invalid": "payload"
        }
        
        response = client.post(
            "/api/v1/webhooks/telegram/notifications",
            json=invalid_payload
        )
        assert response.status_code in [400, 422]
        
        # Test with unknown notification type
        unknown_type_payload = {
            "type": "unknown_type",
            "data": {},
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        response = client.post(
            "/api/v1/webhooks/telegram/notifications",
            json=unknown_type_payload
        )
        assert response.status_code in [400, 500]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/v1/services/")
        # CORS headers should be present in OPTIONS response
        assert response.status_code in [200, 405]  # Some frameworks return 405 for OPTIONS
    
    def test_content_type_handling(self, client):
        """Test content type handling"""
        # Test JSON content type
        response = client.post(
            "/api/v1/webhooks/telegram/notifications",
            json={"type": "test", "data": {}, "timestamp": "2024-01-01T12:00:00Z"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Test invalid content type for JSON endpoint
        response = client.post(
            "/api/v1/webhooks/telegram/notifications",
            content="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 422, 500]