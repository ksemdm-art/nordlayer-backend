"""
Service for cleaning up unused and orphaned files.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.file_service import file_service
from app.models.order import Order

logger = logging.getLogger(__name__)


class FileCleanupService:
    """Service for cleaning up unused files"""
    
    def __init__(self):
        self.upload_dir = Path(file_service.upload_dir)
        logger.info("FileCleanupService initialized")
    
    async def cleanup_orphaned_files(self) -> Dict[str, int]:
        """
        Clean up files that are not referenced in any orders.
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "total_files_checked": 0,
            "orphaned_files_found": 0,
            "orphaned_files_deleted": 0,
            "bytes_freed": 0,
            "errors": 0
        }
        
        try:
            # Get all file URLs from database
            referenced_files = await self._get_referenced_files()
            logger.info(f"Found {len(referenced_files)} files referenced in database")
            
            # Check all files in upload directory
            all_files = self._get_all_uploaded_files()
            stats["total_files_checked"] = len(all_files)
            
            # Find orphaned files
            orphaned_files = []
            for file_path in all_files:
                file_url = self._path_to_url(file_path)
                if file_url not in referenced_files:
                    orphaned_files.append(file_path)
            
            stats["orphaned_files_found"] = len(orphaned_files)
            logger.info(f"Found {len(orphaned_files)} orphaned files")
            
            # Delete orphaned files
            for file_path in orphaned_files:
                try:
                    file_size = file_path.stat().st_size
                    if file_service.delete_file(str(file_path)):
                        stats["orphaned_files_deleted"] += 1
                        stats["bytes_freed"] += file_size
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Error deleting orphaned file {file_path}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during orphaned file cleanup: {e}")
            stats["errors"] += 1
            return stats
    
    async def cleanup_old_temp_files(self, max_age_hours: int = 24) -> Dict[str, int]:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours for temporary files
            
        Returns:
            Dictionary with cleanup statistics
        """
        return await file_service.cleanup_old_files(max_age_hours / 24)
    
    async def cleanup_failed_uploads(self) -> Dict[str, int]:
        """
        Clean up files from failed or incomplete uploads.
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "temp_files_checked": 0,
            "failed_uploads_found": 0,
            "failed_uploads_deleted": 0,
            "bytes_freed": 0,
            "errors": 0
        }
        
        try:
            temp_dir = self.upload_dir / "temp"
            if not temp_dir.exists():
                return stats
            
            # Files older than 1 hour in temp directory are considered failed uploads
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    stats["temp_files_checked"] += 1
                    
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        stats["failed_uploads_found"] += 1
                        
                        try:
                            file_size = file_path.stat().st_size
                            if file_service.delete_file(str(file_path)):
                                stats["failed_uploads_deleted"] += 1
                                stats["bytes_freed"] += file_size
                            else:
                                stats["errors"] += 1
                        except Exception as e:
                            logger.error(f"Error deleting failed upload {file_path}: {e}")
                            stats["errors"] += 1
            
            logger.info(f"Failed upload cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during failed upload cleanup: {e}")
            stats["errors"] += 1
            return stats
    
    async def full_cleanup(self) -> Dict[str, Dict[str, int]]:
        """
        Perform full cleanup including orphaned files, old temp files, and failed uploads.
        
        Returns:
            Dictionary with all cleanup statistics
        """
        logger.info("Starting full file cleanup")
        
        results = {
            "orphaned_files": await self.cleanup_orphaned_files(),
            "old_temp_files": await self.cleanup_old_temp_files(),
            "failed_uploads": await self.cleanup_failed_uploads()
        }
        
        # Calculate totals
        total_deleted = (
            results["orphaned_files"]["orphaned_files_deleted"] +
            results["old_temp_files"]["deleted_files"] +
            results["failed_uploads"]["failed_uploads_deleted"]
        )
        
        total_bytes_freed = (
            results["orphaned_files"]["bytes_freed"] +
            results["old_temp_files"]["bytes_freed"] +
            results["failed_uploads"]["bytes_freed"]
        )
        
        results["totals"] = {
            "total_files_deleted": total_deleted,
            "total_bytes_freed": total_bytes_freed,
            "total_mb_freed": round(total_bytes_freed / (1024 * 1024), 2)
        }
        
        logger.info(f"Full cleanup completed: {results['totals']}")
        return results
    
    async def _get_referenced_files(self) -> Set[str]:
        """Get all file URLs referenced in the database"""
        referenced_files = set()
        
        try:
            db = SessionLocal()
            
            # Get files from orders
            orders = db.query(Order).all()
            
            for order in orders:
                if order.specifications:
                    # Check files_info in specifications
                    files_info = order.specifications.get('files_info', [])
                    for file_info in files_info:
                        if isinstance(file_info, dict) and 'url' in file_info:
                            referenced_files.add(file_info['url'])
                        elif isinstance(file_info, str):
                            referenced_files.add(file_info)
                    
                    # Check other file fields that might exist
                    for key, value in order.specifications.items():
                        if key.endswith('_url') or key.endswith('_file'):
                            if isinstance(value, str) and value.startswith('/uploads/'):
                                referenced_files.add(value)
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error getting referenced files from database: {e}")
        
        return referenced_files
    
    def _get_all_uploaded_files(self) -> List[Path]:
        """Get all files in the upload directory"""
        all_files = []
        
        try:
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    # Skip preview files as they are managed automatically
                    if file_path.parent.name != "previews":
                        all_files.append(file_path)
        
        except Exception as e:
            logger.error(f"Error getting all uploaded files: {e}")
        
        return all_files
    
    def _path_to_url(self, file_path: Path) -> str:
        """Convert file path to URL"""
        try:
            relative_path = file_path.relative_to(self.upload_dir)
            return f"/uploads/{relative_path.as_posix()}"
        except ValueError:
            return str(file_path)
    
    async def get_storage_stats(self) -> Dict[str, any]:
        """Get storage usage statistics"""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "by_category": {},
            "by_folder": {}
        }
        
        try:
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    stats["total_files"] += 1
                    file_size = file_path.stat().st_size
                    stats["total_size_bytes"] += file_size
                    
                    # Category stats
                    extension = file_path.suffix.lower()
                    category = file_service._get_file_category(extension)
                    
                    if category not in stats["by_category"]:
                        stats["by_category"][category] = {"count": 0, "size_bytes": 0}
                    
                    stats["by_category"][category]["count"] += 1
                    stats["by_category"][category]["size_bytes"] += file_size
                    
                    # Folder stats
                    folder = file_path.parent.name
                    if folder not in stats["by_folder"]:
                        stats["by_folder"][folder] = {"count": 0, "size_bytes": 0}
                    
                    stats["by_folder"][folder]["count"] += 1
                    stats["by_folder"][folder]["size_bytes"] += file_size
            
            stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
            
            # Convert bytes to MB for readability
            for category in stats["by_category"]:
                stats["by_category"][category]["size_mb"] = round(
                    stats["by_category"][category]["size_bytes"] / (1024 * 1024), 2
                )
            
            for folder in stats["by_folder"]:
                stats["by_folder"][folder]["size_mb"] = round(
                    stats["by_folder"][folder]["size_bytes"] / (1024 * 1024), 2
                )
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
        
        return stats


# Global cleanup service instance
file_cleanup_service = FileCleanupService()