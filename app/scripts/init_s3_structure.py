#!/usr/bin/env python3
"""
Script to initialize S3 bucket folder structure for the 3D printing platform
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.s3_manager import s3_manager
from app.core.config import settings

# Define the folder structure as specified in the design document
FOLDER_STRUCTURE = [
    "uploads/orders",
    "uploads/projects", 
    "uploads/reviews",
    "uploads/temp",
    "static/placeholders",
    "static/thumbnails"
]

def main():
    """Initialize S3 folder structure"""
    if not settings.use_s3:
        print("S3 is not enabled in configuration. Skipping folder structure creation.")
        return
    
    if not s3_manager:
        print("S3 manager not initialized. Check your S3 configuration.")
        return
    
    print(f"Initializing S3 folder structure in bucket: {settings.s3_bucket_name}")
    print(f"Endpoint: {settings.s3_endpoint_url}")
    
    try:
        # Create folder structure
        success = s3_manager.create_folder_structure(FOLDER_STRUCTURE)
        
        if success:
            print("✅ Successfully created S3 folder structure:")
            for folder in FOLDER_STRUCTURE:
                print(f"   📁 {folder}/")
        else:
            print("❌ Failed to create some folders. Check logs for details.")
            
    except Exception as e:
        print(f"❌ Error initializing S3 structure: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())