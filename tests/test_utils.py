"""
Tests for utility functions
"""
import pytest
import tempfile
import os
from pathlib import Path

from app.core.utils import (
    generate_unique_filename,
    get_file_hash,
    is_allowed_file_type,
    calculate_pagination,
    get_skip_limit,
    format_file_size,
    sanitize_filename,
    validate_file_upload,
    create_response_dict
)
from app.schemas.response import PaginationInfo


class TestFileUtils:
    """Test file-related utility functions"""
    
    def test_generate_unique_filename(self):
        """Test unique filename generation"""
        original = "test_model.stl"
        unique1 = generate_unique_filename(original)
        unique2 = generate_unique_filename(original)
        
        # Should be different
        assert unique1 != unique2
        # Should preserve extension
        assert unique1.endswith(".stl")
        assert unique2.endswith(".stl")
        # Should be valid UUIDs with extension
        assert len(unique1) == 40  # 36 chars UUID + 4 chars extension
    
    def test_get_file_hash(self):
        """Test file hash generation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = get_file_hash(temp_path)
            hash2 = get_file_hash(temp_path)
            
            # Same file should produce same hash
            assert hash1 == hash2
            # Should be SHA-256 (64 hex characters)
            assert len(hash1) == 64
            assert all(c in '0123456789abcdef' for c in hash1)
        finally:
            os.unlink(temp_path)
    
    def test_is_allowed_file_type(self):
        """Test file type validation"""
        # Allowed types
        assert is_allowed_file_type("model.stl") == True
        assert is_allowed_file_type("image.jpg") == True
        assert is_allowed_file_type("IMAGE.JPG") == True  # Case insensitive
        
        # Not allowed types
        assert is_allowed_file_type("document.pdf") == False
        assert is_allowed_file_type("script.exe") == False
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Unsafe characters
        assert sanitize_filename("file/with\\unsafe:chars") == "file_with_unsafe_chars"
        assert sanitize_filename("file*with?quotes\"") == "file_with_quotes_"
        
        # Leading/trailing whitespace and dots
        assert sanitize_filename("  .filename.  ") == "filename."
        
        # Empty filename
        result = sanitize_filename("")
        assert result.startswith("file_")
        assert len(result) > 5
    
    def test_format_file_size(self):
        """Test file size formatting"""
        assert format_file_size(0) == "0B"
        assert format_file_size(1024) == "1.0KB"
        assert format_file_size(1024 * 1024) == "1.0MB"
        assert format_file_size(1536) == "1.5KB"  # 1.5 KB
    
    def test_validate_file_upload(self):
        """Test file upload validation"""
        # Valid file
        result = validate_file_upload("model.stl", 1024)
        assert result["valid"] == True
        assert len(result["errors"]) == 0
        
        # Invalid file type
        result = validate_file_upload("document.pdf", 1024)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert "File type not allowed" in result["errors"][0]
        
        # File too large
        large_size = 100 * 1024 * 1024  # 100MB
        result = validate_file_upload("model.stl", large_size)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert "File too large" in result["errors"][0]


class TestPaginationUtils:
    """Test pagination utility functions"""
    
    def test_calculate_pagination(self):
        """Test pagination calculation"""
        # First page
        pagination = calculate_pagination(page=1, per_page=10, total=25)
        assert pagination.page == 1
        assert pagination.per_page == 10
        assert pagination.total == 25
        assert pagination.pages == 3
        assert pagination.has_next == True
        assert pagination.has_prev == False
        
        # Middle page
        pagination = calculate_pagination(page=2, per_page=10, total=25)
        assert pagination.page == 2
        assert pagination.has_next == True
        assert pagination.has_prev == True
        
        # Last page
        pagination = calculate_pagination(page=3, per_page=10, total=25)
        assert pagination.page == 3
        assert pagination.has_next == False
        assert pagination.has_prev == True
        
        # Exact division
        pagination = calculate_pagination(page=1, per_page=10, total=20)
        assert pagination.pages == 2
        
        # Empty result
        pagination = calculate_pagination(page=1, per_page=10, total=0)
        assert pagination.pages == 0
        assert pagination.has_next == False
        assert pagination.has_prev == False
    
    def test_get_skip_limit(self):
        """Test skip/limit calculation"""
        # First page
        skip, limit = get_skip_limit(page=1, per_page=10)
        assert skip == 0
        assert limit == 10
        
        # Second page
        skip, limit = get_skip_limit(page=2, per_page=10)
        assert skip == 10
        assert limit == 10
        
        # Third page with different per_page
        skip, limit = get_skip_limit(page=3, per_page=5)
        assert skip == 10
        assert limit == 5


class TestResponseUtils:
    """Test response utility functions"""
    
    def test_create_response_dict(self):
        """Test response dictionary creation"""
        # Basic response
        response = create_response_dict()
        assert response["success"] == True
        assert "timestamp" in response
        
        # Response with data
        response = create_response_dict(data={"test": "value"})
        assert response["data"] == {"test": "value"}
        
        # Response with message
        response = create_response_dict(message="Test message")
        assert response["message"] == "Test message"
        
        # Response with pagination
        pagination = PaginationInfo(
            page=1, per_page=10, total=25, pages=3, 
            has_next=True, has_prev=False
        )
        response = create_response_dict(pagination=pagination)
        assert "pagination" in response
        assert response["pagination"]["page"] == 1
        
        # Error response
        response = create_response_dict(success=False, message="Error occurred")
        assert response["success"] == False
        assert response["message"] == "Error occurred"
        
        # Additional fields
        response = create_response_dict(custom_field="custom_value")
        assert response["custom_field"] == "custom_value"