"""S3 Storage integration for file uploads."""
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import os
from pathlib import Path
import mimetypes

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class S3Storage:
    """S3 storage client for file operations."""
    
    def __init__(self):
        """Initialize S3 client."""
        self.endpoint_url = os.getenv('S3_ENDPOINT_URL')
        self.access_key = os.getenv('S3_ACCESS_KEY_ID')
        self.secret_key = os.getenv('S3_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.region = os.getenv('S3_REGION', 'ru-1')
        
        if not all([self.endpoint_url, self.access_key, self.secret_key, self.bucket_name]):
            logger.warning("S3 credentials not configured. File uploads will be disabled.")
            self.client = None
            return
        
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version='s3v4')
            )
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.client = None
    
    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        folder: str = "uploads",
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload file to S3.
        
        Args:
            file: File object to upload
            filename: Name of the file
            folder: Folder path in bucket
            content_type: MIME type of the file
            
        Returns:
            Public URL of uploaded file or None if failed
        """
        if not self.client:
            logger.error("S3 client not initialized")
            return None
        
        try:
            # Generate object key
            object_key = f"{folder}/{filename}"
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Upload file
            self.client.upload_fileobj(
                file,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            # Generate public URL
            url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            logger.info(f"File uploaded successfully: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return None
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            file_url: Full URL of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            # Extract object key from URL
            # URL format: https://s3.twcstorage.ru/bucket-name/folder/filename
            parts = file_url.replace(f"{self.endpoint_url}/{self.bucket_name}/", "")
            object_key = parts
            
            # Delete object
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"File deleted successfully: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {e}")
            return False
    
    def file_exists(self, file_url: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            file_url: Full URL of the file
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.client:
            return False
        
        try:
            parts = file_url.replace(f"{self.endpoint_url}/{self.bucket_name}/", "")
            object_key = parts
            
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError:
            return False


# Global S3 storage instance
s3_storage = S3Storage()
