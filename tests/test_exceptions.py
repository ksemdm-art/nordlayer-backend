"""
Tests for custom exceptions
"""
import pytest
from fastapi import status

from app.core.exceptions import (
    APIError,
    ValidationError,
    NotFoundError,
    FileUploadError,
    OrderValidationError,
    AuthenticationError,
    AuthorizationError
)


class TestAPIError:
    """Test base APIError class"""
    
    def test_api_error_creation(self):
        """Test APIError creation with default values"""
        error = APIError("Test error")
        assert error.message == "Test error"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.details == {}
    
    def test_api_error_with_custom_values(self):
        """Test APIError creation with custom values"""
        details = {"field": "value"}
        error = APIError("Custom error", status_code=422, details=details)
        assert error.message == "Custom error"
        assert error.status_code == 422
        assert error.details == details
    
    def test_api_error_string_representation(self):
        """Test APIError string representation"""
        error = APIError("Test error")
        assert str(error) == "Test error"


class TestValidationError:
    """Test ValidationError class"""
    
    def test_validation_error_creation(self):
        """Test ValidationError creation"""
        error = ValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert error.details == {}
    
    def test_validation_error_with_details(self):
        """Test ValidationError with details"""
        details = {"field": "required", "value": "invalid"}
        error = ValidationError("Validation failed", details=details)
        assert error.details == details


class TestNotFoundError:
    """Test NotFoundError class"""
    
    def test_not_found_error_without_identifier(self):
        """Test NotFoundError without identifier"""
        error = NotFoundError("User")
        assert error.message == "User not found"
        assert error.status_code == status.HTTP_404_NOT_FOUND
    
    def test_not_found_error_with_identifier(self):
        """Test NotFoundError with identifier"""
        error = NotFoundError("User", 123)
        assert error.message == "User not found with id: 123"
        assert error.status_code == status.HTTP_404_NOT_FOUND
    
    def test_not_found_error_with_string_identifier(self):
        """Test NotFoundError with string identifier"""
        error = NotFoundError("Project", "abc-123")
        assert error.message == "Project not found with id: abc-123"


class TestFileUploadError:
    """Test FileUploadError class"""
    
    def test_file_upload_error_creation(self):
        """Test FileUploadError creation"""
        error = FileUploadError("File upload failed")
        assert error.message == "File upload failed"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_file_upload_error_with_details(self):
        """Test FileUploadError with details"""
        details = {"filename": "test.pdf", "reason": "invalid_type"}
        error = FileUploadError("Invalid file type", details=details)
        assert error.details == details


class TestOrderValidationError:
    """Test OrderValidationError class"""
    
    def test_order_validation_error_creation(self):
        """Test OrderValidationError creation"""
        error = OrderValidationError("Order validation failed")
        assert error.message == "Order validation failed"
        assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_order_validation_error_with_details(self):
        """Test OrderValidationError with details"""
        details = {"customer_name": "required", "files": "at_least_one"}
        error = OrderValidationError("Missing required fields", details=details)
        assert error.details == details


class TestAuthenticationError:
    """Test AuthenticationError class"""
    
    def test_authentication_error_default_message(self):
        """Test AuthenticationError with default message"""
        error = AuthenticationError()
        assert error.message == "Authentication required"
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message"""
        error = AuthenticationError("Invalid token")
        assert error.message == "Invalid token"
        assert error.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthorizationError:
    """Test AuthorizationError class"""
    
    def test_authorization_error_default_message(self):
        """Test AuthorizationError with default message"""
        error = AuthorizationError()
        assert error.message == "Insufficient permissions"
        assert error.status_code == status.HTTP_403_FORBIDDEN
    
    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message"""
        error = AuthorizationError("Admin access required")
        assert error.message == "Admin access required"
        assert error.status_code == status.HTTP_403_FORBIDDEN


class TestExceptionInheritance:
    """Test exception inheritance and behavior"""
    
    def test_all_exceptions_inherit_from_api_error(self):
        """Test that all custom exceptions inherit from APIError"""
        exceptions = [
            ValidationError("test"),
            NotFoundError("test"),
            FileUploadError("test"),
            OrderValidationError("test"),
            AuthenticationError("test"),
            AuthorizationError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, APIError)
            assert isinstance(exc, Exception)
    
    def test_exceptions_can_be_raised_and_caught(self):
        """Test that exceptions can be raised and caught properly"""
        with pytest.raises(APIError):
            raise ValidationError("Test validation error")
        
        with pytest.raises(ValidationError):
            raise ValidationError("Test validation error")
        
        # Test catching specific exception type
        try:
            raise NotFoundError("User", 123)
        except NotFoundError as e:
            assert e.message == "User not found with id: 123"
        except Exception:
            pytest.fail("Should have caught NotFoundError specifically")
    
    def test_exception_details_are_preserved(self):
        """Test that exception details are preserved when raised"""
        details = {"field": "test", "value": 123}
        
        try:
            raise ValidationError("Test error", details=details)
        except ValidationError as e:
            assert e.details == details
            assert e.message == "Test error"
            assert e.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY