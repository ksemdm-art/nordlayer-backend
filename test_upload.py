#!/usr/bin/env python3
"""
Test file upload to verify S3 integration
"""

import sys
from pathlib import Path
import asyncio
import tempfile
from io import BytesIO

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.services.s3_manager import s3_manager
from fastapi import UploadFile

import pytest

@pytest.mark.asyncio
async def test_file_upload():
    """Test file upload to S3"""
    print("Testing file upload...")
    print(f"S3 Enabled: {settings.use_s3}")
    print(f"S3 Manager: {s3_manager is not None}")
    
    if not settings.use_s3 or not s3_manager:
        print("❌ S3 not available")
        return False
    
    try:
        # Create a test image file
        test_content = b"fake image content for testing"
        test_file = BytesIO(test_content)
        
        # Create UploadFile-like object
        class MockUploadFile:
            def __init__(self, content, filename, content_type):
                self.file = BytesIO(content)
                self.filename = filename
                self.content_type = content_type
                self.size = len(content)
            
            async def seek(self, position):
                self.file.seek(position)
            
            async def read(self):
                return self.file.read()
        
        mock_file = MockUploadFile(test_content, "test.jpg", "image/jpeg")
        
        # Upload file
        print("\nUploading test file...")
        file_url = await s3_manager.upload_file(mock_file, "uploads/test", validate=False)
        
        print(f"✅ File uploaded successfully!")
        print(f"URL: {file_url}")
        
        # Verify URL format
        expected_prefix = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/"
        if file_url.startswith(expected_prefix):
            print("✅ URL format is correct")
        else:
            print(f"❌ URL format incorrect. Expected prefix: {expected_prefix}")
            return False
        
        # Clean up - delete the test file
        print("\nCleaning up...")
        deleted = s3_manager.delete_file(file_url)
        if deleted:
            print("✅ Test file deleted successfully")
        else:
            print("⚠️ Could not delete test file")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload test failed: {str(e)}")
        return False

def main():
    """Run the upload test"""
    result = asyncio.run(test_file_upload())
    return 0 if result else 1

if __name__ == "__main__":
    exit(main())