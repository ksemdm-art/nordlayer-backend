"""
File service for handling file operations, validation, and cleanup.
"""
import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import aiofiles
from fastapi import UploadFile, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations and management"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.temp_dir = self.upload_dir / "temp"
        self.orders_dir = self.upload_dir / "orders"
        self.previews_dir = self.upload_dir / "previews"
        
        for directory in [self.temp_dir, self.orders_dir, self.previews_dir]:
            directory.mkdir(exist_ok=True)
        
        logger.info(f"FileService initialized with upload_dir: {self.upload_dir}")
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded file for type, size, and other constraints.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Dict with validation results
            
        Raises:
            HTTPException: If validation fails
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_extension}' not allowed. Allowed types: {settings.allowed_file_types}"
            )
        
        # Check file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size / (1024*1024):.1f} MB"
            )
        
        # Determine file category
        file_category = self._get_file_category(file_extension)
        
        return {
            "filename": file.filename,
            "extension": file_extension,
            "size": file.size,
            "category": file_category,
            "is_valid": True
        }
    
    def _get_file_category(self, extension: str) -> str:
        """Determine file category based on extension"""
        model_extensions = ['.stl', '.obj', '.3mf', '.ply', '.gcode']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        if extension in model_extensions:
            return "model"
        elif extension in image_extensions:
            return "image"
        else:
            return "other"
    
    async def save_file(
        self, 
        file: UploadFile, 
        folder: str = "temp",
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save uploaded file to specified folder.
        
        Args:
            file: FastAPI UploadFile object
            folder: Subfolder within upload directory
            custom_filename: Optional custom filename (will generate UUID if not provided)
            
        Returns:
            Dict with file information
        """
        # Validate file first
        validation_result = self.validate_file(file)
        
        # Generate filename
        if custom_filename:
            filename = custom_filename
        else:
            file_extension = validation_result["extension"]
            filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create folder path
        folder_path = self.upload_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Full file path
        file_path = folder_path / filename
        
        # Save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Generate file URL
        file_url = f"/uploads/{folder}/{filename}"
        
        # Generate preview for images
        preview_url = None
        if validation_result["category"] == "image":
            preview_url = await self._generate_image_preview(file_path, filename)
        
        logger.info(f"File saved: {file_path}")
        
        return {
            "filename": filename,
            "original_filename": file.filename,
            "path": str(file_path),
            "url": file_url,
            "preview_url": preview_url,
            "size": len(content),
            "category": validation_result["category"],
            "extension": validation_result["extension"],
            "created_at": datetime.now().isoformat()
        }
    
    async def save_order_files(
        self, 
        order_id: int, 
        files: List[UploadFile],
        file_type: str = "models"
    ) -> List[Dict[str, Any]]:
        """
        Save multiple files for a specific order.
        
        Args:
            order_id: Order ID
            files: List of UploadFile objects
            file_type: Type of files (models, images, etc.)
            
        Returns:
            List of file information dictionaries
        """
        folder = f"orders/{order_id}/{file_type}"
        saved_files = []
        
        for file in files:
            try:
                file_info = await self.save_file(file, folder)
                saved_files.append(file_info)
            except Exception as e:
                logger.error(f"Failed to save file {file.filename}: {e}")
                # Continue with other files, but log the error
                continue
        
        logger.info(f"Saved {len(saved_files)} files for order {order_id}")
        return saved_files
    
    async def _generate_image_preview(self, image_path: Path, filename: str) -> Optional[str]:
        """
        Generate preview/thumbnail for image files.
        
        Args:
            image_path: Path to the original image
            filename: Original filename
            
        Returns:
            Preview URL or None if generation failed
        """
        try:
            # Create preview filename
            name_without_ext = Path(filename).stem
            preview_filename = f"{name_without_ext}_preview.jpg"
            preview_path = self.previews_dir / preview_filename
            
            # Generate thumbnail using PIL
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail (max 300x300, maintain aspect ratio)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # Auto-orient based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Save as JPEG with good quality
                img.save(preview_path, 'JPEG', quality=85, optimize=True)
            
            preview_url = f"/uploads/previews/{preview_filename}"
            logger.info(f"Generated preview: {preview_path}")
            
            return preview_url
            
        except Exception as e:
            logger.error(f"Failed to generate preview for {filename}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from filesystem.
        
        Args:
            file_path: Path to file (can be relative or absolute)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Handle both absolute and relative paths
            if file_path.startswith('/uploads/'):
                # Remove leading slash and convert to Path
                relative_path = file_path[1:]  # Remove leading /
                full_path = Path(relative_path)
            else:
                full_path = Path(file_path)
            
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.info(f"Deleted file: {full_path}")
                
                # Also delete preview if it exists
                if full_path.parent.name != "previews":
                    preview_filename = f"{full_path.stem}_preview.jpg"
                    preview_path = self.previews_dir / preview_filename
                    if preview_path.exists():
                        preview_path.unlink()
                        logger.info(f"Deleted preview: {preview_path}")
                
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def list_files(self, folder: str = "") -> List[Dict[str, Any]]:
        """
        List files in specified folder.
        
        Args:
            folder: Subfolder to list (empty for root upload directory)
            
        Returns:
            List of file information dictionaries
        """
        try:
            if folder:
                search_path = self.upload_dir / folder
            else:
                search_path = self.upload_dir
            
            if not search_path.exists():
                return []
            
            files = []
            for file_path in search_path.rglob('*'):
                if file_path.is_file():
                    # Skip preview files in main listing
                    if file_path.parent.name == "previews":
                        continue
                    
                    relative_path = file_path.relative_to(self.upload_dir)
                    file_url = f"/uploads/{relative_path.as_posix()}"
                    
                    # Check for preview
                    preview_url = None
                    if self._get_file_category(file_path.suffix.lower()) == "image":
                        preview_filename = f"{file_path.stem}_preview.jpg"
                        preview_path = self.previews_dir / preview_filename
                        if preview_path.exists():
                            preview_url = f"/uploads/previews/{preview_filename}"
                    
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "url": file_url,
                        "preview_url": preview_url,
                        "size": stat.st_size,
                        "category": self._get_file_category(file_path.suffix.lower()),
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return sorted(files, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing files in {folder}: {e}")
            return []
    
    async def cleanup_old_files(self, max_age_days: int = 7) -> Dict[str, int]:
        """
        Clean up old temporary files.
        
        Args:
            max_age_days: Maximum age in days for temporary files
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        total_size_freed = 0
        
        try:
            # Only clean up temp directory
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        
                        if self.delete_file(str(file_path)):
                            deleted_count += 1
                            total_size_freed += file_size
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted, {total_size_freed} bytes freed")
            
            return {
                "deleted_files": deleted_count,
                "bytes_freed": total_size_freed,
                "mb_freed": round(total_size_freed / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            return {"deleted_files": 0, "bytes_freed": 0, "mb_freed": 0}
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific file.
        
        Args:
            file_path: Path to file
            
        Returns:
            File information dictionary or None if file doesn't exist
        """
        try:
            # Handle both absolute and relative paths
            if file_path.startswith('/uploads/'):
                relative_path = file_path[1:]
                full_path = Path(relative_path)
            else:
                full_path = Path(file_path)
            
            if not full_path.exists() or not full_path.is_file():
                return None
            
            stat = full_path.stat()
            
            # Check for preview
            preview_url = None
            if self._get_file_category(full_path.suffix.lower()) == "image":
                preview_filename = f"{full_path.stem}_preview.jpg"
                preview_path = self.previews_dir / preview_filename
                if preview_path.exists():
                    preview_url = f"/uploads/previews/{preview_filename}"
            
            return {
                "filename": full_path.name,
                "path": str(full_path),
                "url": f"/uploads/{full_path.relative_to(self.upload_dir).as_posix()}",
                "preview_url": preview_url,
                "size": stat.st_size,
                "category": self._get_file_category(full_path.suffix.lower()),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None


# Global file service instance
file_service = FileService()