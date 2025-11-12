"""
Tests for basic API structure and middleware
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.exceptions import APIError, ValidationError, NotFoundError


client = TestClient(app)


class TestBasicAPIStructure:
    """Test basic API structure and endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "3D Printing Platform API"}
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_api_docs_available_in_development(self):
        """Test that API docs are available in development"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_cors_headers_present(self):
        """Test that CORS headers are properly set"""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        # CORS preflight should be handled
        assert "access-control-allow-origin" in response.headers
    
    def test_security_headers_present(self):
        """Test that security headers are added by middleware"""
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "X-Request-ID" in response.headers
    
    def test_request_id_header_present(self):
        """Test that request ID is added to response headers"""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0


class TestExceptionHandling:
    """Test centralized exception handling"""
    
    def test_api_error_handling(self):
        """Test that APIError is properly handled"""
        # Create a test endpoint that raises APIError
        @app.get("/test-api-error")
        async def test_api_error():
            raise APIError("Test API error", status_code=400, details={"field": "test"})
        
        response = client.get("/test-api-error")
        assert response.status_code == 400
        
        json_response = response.json()
        assert json_response["error"]["message"] == "Test API error"
        assert json_response["error"]["details"] == {"field": "test"}
        assert json_response["error"]["type"] == "APIError"
    
    def test_validation_error_handling(self):
        """Test that ValidationError is properly handled"""
        @app.get("/test-validation-error")
        async def test_validation_error():
            raise ValidationError("Test validation error", details={"field": "required"})
        
        response = client.get("/test-validation-error")
        assert response.status_code == 422
        
        json_response = response.json()
        assert json_response["error"]["message"] == "Test validation error"
        assert json_response["error"]["details"] == {"field": "required"}
        assert json_response["error"]["type"] == "ValidationError"
    
    def test_not_found_error_handling(self):
        """Test that NotFoundError is properly handled"""
        @app.get("/test-not-found-error")
        async def test_not_found_error():
            raise NotFoundError("TestResource", "123")
        
        response = client.get("/test-not-found-error")
        assert response.status_code == 404
        
        json_response = response.json()
        assert "TestResource not found with id: 123" in json_response["error"]["message"]
        assert json_response["error"]["type"] == "NotFoundError"
    
    def test_unexpected_error_handling(self):
        """Test that unexpected errors are properly handled"""
        @app.get("/test-unexpected-error")
        async def test_unexpected_error():
            raise ValueError("Unexpected error")
        
        response = client.get("/test-unexpected-error")
        assert response.status_code == 500
        
        json_response = response.json()
        assert json_response["error"]["message"] == "Internal server error"
        assert json_response["error"]["type"] == "InternalServerError"
        assert "request_id" in json_response["error"]
    
    def test_pydantic_validation_error_handling(self):
        """Test that Pydantic validation errors are properly handled"""
        # This will be tested when we have actual endpoints with Pydantic models
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


class TestMiddleware:
    """Test custom middleware functionality"""
    
    def test_logging_middleware_adds_request_id(self):
        """Test that logging middleware adds request ID"""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        # UUID format check (basic)
        assert len(request_id) == 36
        assert request_id.count("-") == 4
    
    @patch('app.core.middleware.logger')
    def test_logging_middleware_logs_requests(self, mock_logger):
        """Test that requests are logged"""
        client.get("/")
        # Check that logger.info was called for request and response
        assert mock_logger.info.call_count >= 2
    
    def test_security_headers_middleware(self):
        """Test that security headers are added"""
        response = client.get("/")
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        for header, value in expected_headers.items():
            assert response.headers.get(header) == value


class TestAPIRouterStructure:
    """Test API router structure"""
    
    def test_api_v1_prefix(self):
        """Test that API v1 prefix is properly configured"""
        # Test that endpoints are accessible under /api/v1
        response = client.get("/api/v1/projects")
        # Should return 200 or 404, but not 405 (method not allowed)
        assert response.status_code in [200, 404]
    
    def test_router_tags_configuration(self):
        """Test that router tags are properly configured"""
        # This can be verified by checking the OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        # Check that tags are defined
        tags = [tag["name"] for tag in openapi_schema.get("tags", [])]
        expected_tags = ["projects", "orders", "articles", "services"]
        
        for tag in expected_tags:
            assert tag in tags or len([path for path in openapi_schema["paths"].values() 
                                     for method in path.values() 
                                     if tag in method.get("tags", [])]) > 0