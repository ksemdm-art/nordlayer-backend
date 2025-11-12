import boto3
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3FileManager:
    """Service for managing files in S3 storage"""
    
    def __init__(self):
        """Initialize S3 client with Yandex Cloud configuration"""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region
            )
            self.bucket_name = settings.s3_bucket_name
            self._ensure_bucket_exists()
            logger.info("S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise Exception(f"S3 storage configuration error: {str(e)}")
    
    def _ensure_bucket_exists(self):
        """Ensure the S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket {self.bucket_name} is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket {self.bucket_name} does not exist")
                raise Exception(f"Storage bucket not found: {self.bucket_name}")
            else:
                logger.error(f"Error accessing bucket: {str(e)}")
                raise Exception(f"Storage access error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking bucket: {str(e)}")
            raise Exception(f"Storage configuration error: {str(e)}")
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename preserving extension"""
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate file type and size"""
        # Check file size
        if hasattr(file, 'size') and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size / (1024*1024):.0f}MB"
            )
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_file_types)}"
            )
    
    async def upload_file(
        self, 
        file: UploadFile, 
        folder: str,
        filename: Optional[str] = None,
        validate: bool = True
    ) -> str:
        """
        Upload file to S3 and return public URL
        
        Args:
            file: FastAPI UploadFile object
            folder: S3 folder path (e.g., 'uploads/orders/123/models')
            filename: Optional custom filename, if not provided generates unique name
            validate: Whether to validate file type and size
            
        Returns:
            Public URL of uploaded file
        """
        if validate:
            self._validate_file(file)
        
        if not filename:
            filename = self._generate_unique_filename(file.filename)
        
        # Construct S3 key
        key = f"{folder.strip('/')}/{filename}"
        
        try:
            # Reset file pointer to beginning
            await file.seek(0)
            
            # Read file content
            file_content = await file.read()
            
            # Upload file to S3 using put_object instead of upload_fileobj
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=file.content_type or 'application/octet-stream',
                ACL='public-read'  # Make file publicly accessible
            )
            
            # Return public URL
            return f"{settings.s3_endpoint_url}/{self.bucket_name}/{key}"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload error: {error_code} - {str(e)}")
            
            if error_code == 'EntityTooLarge':
                raise HTTPException(
                    status_code=413,
                    detail="File too large for storage"
                )
            elif error_code == 'AccessDenied':
                raise HTTPException(
                    status_code=500,
                    detail="Storage access denied"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="File upload failed"
                )
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="File upload failed"
            )
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from S3 using its URL
        
        Args:
            file_url: Full URL of the file to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Extract key from URL
            if f"{settings.s3_endpoint_url}/{self.bucket_name}/" in file_url:
                key = file_url.split(f"{settings.s3_endpoint_url}/{self.bucket_name}/")[1]
            else:
                logger.warning(f"Invalid S3 URL format: {file_url}")
                return False
            
            # Delete object from S3
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted file: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file {file_url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file_url}: {str(e)}")
            return False
    
    def get_file_url(self, key: str) -> str:
        """
        Get public URL for a file by its S3 key
        
        Args:
            key: S3 object key
            
        Returns:
            Public URL of the file
        """
        return f"{settings.s3_endpoint_url}/{self.bucket_name}/{key}"
    
    def generate_presigned_url(
        self, 
        key: str, 
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> str:
        """
        Generate presigned URL for secure file access
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            method: S3 method ('get_object' for download, 'put_object' for upload)
            
        Returns:
            Presigned URL
        """
        try:
            response = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate secure file URL"
            )
    
    def list_files(self, prefix: str = "") -> List[dict]:
        """
        List files in S3 bucket with optional prefix filter
        
        Args:
            prefix: S3 key prefix to filter files
            
        Returns:
            List of file information dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': self.get_file_url(obj['Key'])
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to list files"
            )
    
    def create_folder_structure(self, base_folders: List[str]) -> bool:
        """
        Create folder structure in S3 by uploading placeholder files
        
        Args:
            base_folders: List of folder paths to create
            
        Returns:
            True if successful
        """
        try:
            for folder in base_folders:
                # S3 doesn't have folders, but we can create a placeholder file
                placeholder_key = f"{folder.strip('/')}/placeholder.txt"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=placeholder_key,
                    Body=b"This is a placeholder file to maintain folder structure.",
                    ContentType='text/plain'
                )
            
            logger.info(f"Created folder structure: {base_folders}")
            return True
            
        except ClientError as e:
            logger.error(f"Error creating folder structure: {str(e)}")
            return False

# Global instance - initialize with error handling
def _initialize_s3_manager():
    """Initialize S3 manager with proper error handling"""
    if not settings.use_s3:
        return None
    
    try:
        return S3FileManager()
    except Exception as e:
        logger.warning(f"S3 initialization failed: {str(e)}. Falling back to local storage.")
        return None

s3_manager = _initialize_s3_manager()