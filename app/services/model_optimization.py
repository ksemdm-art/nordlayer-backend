"""
Service for optimizing 3D model loading and processing.
"""
import os
import gzip
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import hashlib

from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class ModelOptimizationService:
    """Service for optimizing 3D model files"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.optimized_dir = self.upload_dir / "optimized"
        self.optimized_dir.mkdir(exist_ok=True)
        logger.info("ModelOptimizationService initialized")
    
    async def get_optimized_model_url(self, original_file_path: str) -> Optional[str]:
        """
        Get optimized version of 3D model or create one if it doesn't exist.
        
        Args:
            original_file_path: Path to original model file
            
        Returns:
            URL to optimized model or None if optimization failed
        """
        try:
            # Generate cache key based on file path and modification time
            file_path = Path(original_file_path)
            if not file_path.exists():
                logger.warning(f"Original file not found: {original_file_path}")
                return None
            
            # Get file stats for cache invalidation
            file_stat = file_path.stat()
            file_hash = hashlib.md5(
                f"{original_file_path}:{file_stat.st_mtime}:{file_stat.st_size}".encode()
            ).hexdigest()
            
            cache_key = f"model_optimization:{file_hash}"
            
            # Check if optimized version exists in cache
            cached_url = await cache_service.get(cache_key)
            if cached_url:
                optimized_path = Path(cached_url.replace('/uploads/', ''))
                if optimized_path.exists():
                    return cached_url
            
            # Create optimized version
            optimized_url = await self._create_optimized_model(file_path, file_hash)
            
            if optimized_url:
                # Cache the result for 24 hours
                await cache_service.set(cache_key, optimized_url, 86400)
            
            return optimized_url
            
        except Exception as e:
            logger.error(f"Error optimizing model {original_file_path}: {e}")
            return None
    
    async def _create_optimized_model(self, file_path: Path, file_hash: str) -> Optional[str]:
        """
        Create optimized version of 3D model.
        
        Args:
            file_path: Path to original model file
            file_hash: Hash for unique filename
            
        Returns:
            URL to optimized model or None if failed
        """
        try:
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.stl':
                return await self._optimize_stl_file(file_path, file_hash)
            elif file_extension == '.obj':
                return await self._optimize_obj_file(file_path, file_hash)
            elif file_extension == '.3mf':
                return await self._optimize_3mf_file(file_path, file_hash)
            else:
                logger.warning(f"Unsupported file type for optimization: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating optimized model: {e}")
            return None
    
    async def _optimize_stl_file(self, file_path: Path, file_hash: str) -> Optional[str]:
        """
        Optimize STL file by compressing it.
        
        Args:
            file_path: Path to original STL file
            file_hash: Hash for unique filename
            
        Returns:
            URL to optimized STL file
        """
        try:
            # Create compressed version
            optimized_filename = f"{file_hash}_optimized.stl.gz"
            optimized_path = self.optimized_dir / optimized_filename
            
            # Compress the STL file
            with open(file_path, 'rb') as f_in:
                with gzip.open(optimized_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Check compression ratio
            original_size = file_path.stat().st_size
            compressed_size = optimized_path.stat().st_size
            compression_ratio = compressed_size / original_size
            
            logger.info(f"STL compressed: {original_size} -> {compressed_size} bytes "
                       f"(ratio: {compression_ratio:.2f})")
            
            # If compression doesn't save much space, use original
            if compression_ratio > 0.9:
                optimized_path.unlink()  # Delete compressed version
                return f"/uploads/{file_path.relative_to(self.upload_dir).as_posix()}"
            
            return f"/uploads/optimized/{optimized_filename}"
            
        except Exception as e:
            logger.error(f"Error optimizing STL file: {e}")
            return None
    
    async def _optimize_obj_file(self, file_path: Path, file_hash: str) -> Optional[str]:
        """
        Optimize OBJ file by removing comments and unnecessary whitespace.
        
        Args:
            file_path: Path to original OBJ file
            file_hash: Hash for unique filename
            
        Returns:
            URL to optimized OBJ file
        """
        try:
            optimized_filename = f"{file_hash}_optimized.obj"
            optimized_path = self.optimized_dir / optimized_filename
            
            # Read and optimize OBJ file
            with open(file_path, 'r', encoding='utf-8') as f_in:
                with open(optimized_path, 'w', encoding='utf-8') as f_out:
                    for line in f_in:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            f_out.write(line + '\n')
            
            # Check if optimization was beneficial
            original_size = file_path.stat().st_size
            optimized_size = optimized_path.stat().st_size
            
            if optimized_size >= original_size * 0.95:  # Less than 5% savings
                optimized_path.unlink()
                return f"/uploads/{file_path.relative_to(self.upload_dir).as_posix()}"
            
            logger.info(f"OBJ optimized: {original_size} -> {optimized_size} bytes")
            return f"/uploads/optimized/{optimized_filename}"
            
        except Exception as e:
            logger.error(f"Error optimizing OBJ file: {e}")
            return None
    
    async def _optimize_3mf_file(self, file_path: Path, file_hash: str) -> Optional[str]:
        """
        3MF files are already compressed, so just return original.
        
        Args:
            file_path: Path to original 3MF file
            file_hash: Hash for unique filename
            
        Returns:
            URL to original 3MF file
        """
        # 3MF files are already compressed ZIP archives
        return f"/uploads/{file_path.relative_to(self.upload_dir).as_posix()}"
    
    async def get_model_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about 3D model file.
        
        Args:
            file_path: Path to model file
            
        Returns:
            Dictionary with model information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": "File not found"}
            
            file_stat = path.stat()
            file_extension = path.suffix.lower()
            
            info = {
                "filename": path.name,
                "size_bytes": file_stat.st_size,
                "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "format": file_extension,
                "modified_at": file_stat.st_mtime,
                "is_optimizable": file_extension in ['.stl', '.obj']
            }
            
            # Try to get additional info based on file type
            if file_extension == '.stl':
                info.update(await self._get_stl_info(path))
            elif file_extension == '.obj':
                info.update(await self._get_obj_info(path))
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting model info for {file_path}: {e}")
            return {"error": str(e)}
    
    async def _get_stl_info(self, file_path: Path) -> Dict[str, Any]:
        """Get STL-specific information"""
        try:
            # Basic STL info - could be extended with actual STL parsing
            return {
                "type": "STL (Stereolithography)",
                "description": "Binary or ASCII STL file for 3D printing"
            }
        except Exception as e:
            logger.error(f"Error getting STL info: {e}")
            return {}
    
    async def _get_obj_info(self, file_path: Path) -> Dict[str, Any]:
        """Get OBJ-specific information"""
        try:
            vertex_count = 0
            face_count = 0
            
            # Count vertices and faces
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('v '):
                        vertex_count += 1
                    elif line.startswith('f '):
                        face_count += 1
            
            return {
                "type": "OBJ (Wavefront)",
                "description": "Wavefront OBJ 3D model file",
                "vertices": vertex_count,
                "faces": face_count
            }
        except Exception as e:
            logger.error(f"Error getting OBJ info: {e}")
            return {}
    
    async def cleanup_old_optimized_files(self, max_age_days: int = 7) -> Dict[str, int]:
        """
        Clean up old optimized files.
        
        Args:
            max_age_days: Maximum age in days for optimized files
            
        Returns:
            Dictionary with cleanup statistics
        """
        from datetime import datetime, timedelta
        
        stats = {
            "files_checked": 0,
            "files_deleted": 0,
            "bytes_freed": 0
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            for file_path in self.optimized_dir.rglob('*'):
                if file_path.is_file():
                    stats["files_checked"] += 1
                    
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats["files_deleted"] += 1
                        stats["bytes_freed"] += file_size
            
            logger.info(f"Optimized files cleanup: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during optimized files cleanup: {e}")
            return stats


# Global model optimization service instance
model_optimization_service = ModelOptimizationService()