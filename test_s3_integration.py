#!/usr/bin/env python3
"""
Simple test script to verify S3 integration is working
"""

import sys
from pathlib import Path
import asyncio
from io import BytesIO

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.services.s3_manager import s3_manager

import pytest

@pytest.mark.asyncio
async def test_s3_integration():
    """Test basic S3 operations"""
    print("Testing S3 Integration...")
    print(f"S3 Enabled: {settings.use_s3}")
    print(f"Bucket: {settings.s3_bucket_name}")
    print(f"Endpoint: {settings.s3_endpoint_url}")
    
    if not settings.use_s3:
        print("❌ S3 is not enabled in configuration")
        return False
    
    if not s3_manager:
        print("❌ S3 manager not initialized")
        return False
    
    try:
        # Test 1: List files (should work even if bucket is empty)
        print("\n1. Testing file listing...")
        files = s3_manager.list_files("uploads/")
        print(f"✅ Found {len(files)} files in uploads/ folder")
        
        # Test 2: Create folder structure
        print("\n2. Testing folder structure creation...")
        test_folders = ["test/folder1", "test/folder2"]
        success = s3_manager.create_folder_structure(test_folders)
        if success:
            print("✅ Folder structure created successfully")
        else:
            print("❌ Failed to create folder structure")
            return False
        
        # Test 3: Generate file URL
        print("\n3. Testing URL generation...")
        test_url = s3_manager.get_file_url("test/sample.txt")
        expected_prefix = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/"
        if test_url.startswith(expected_prefix):
            print(f"✅ URL generation works: {test_url}")
        else:
            print(f"❌ URL generation failed: {test_url}")
            return False
        
        print("\n✅ All S3 integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ S3 integration test failed: {str(e)}")
        return False

def main():
    """Run the S3 integration test"""
    result = asyncio.run(test_s3_integration())
    return 0 if result else 1

if __name__ == "__main__":
    exit(main())