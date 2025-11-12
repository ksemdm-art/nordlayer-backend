"""
Utility functions for the application
"""
import os
import uuid
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.schemas.response import PaginationInfo


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension"""
    file_extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_extension}"


def get_file_hash(file_path: str) -> str:
    """Generate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def ensure_upload_directory() -> str:
    """Ensure upload directory exists and return path"""
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return str(upload_path)


def is_allowed_file_type(filename: str) -> bool:
    """Check if file type is allowed"""
    file_extension = Path(filename).suffix.lower()
    return file_extension in settings.allowed_file_types


def calculate_pagination(
    page: int, 
    per_page: int, 
    total: int
) -> PaginationInfo:
    """Calculate pagination information"""
    pages = (total + per_page - 1) // per_page  # Ceiling division
    has_next = page < pages
    has_prev = page > 1
    
    return PaginationInfo(
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


def get_skip_limit(page: int, per_page: int) -> tuple[int, int]:
    """Convert page/per_page to skip/limit for database queries"""
    skip = (page - 1) * per_page
    return skip, per_page


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing unsafe characters"""
    # Remove path separators and other unsafe characters
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = filename
    
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing whitespace but preserve trailing dots in filename
    sanitized = sanitized.strip(' ')
    # Only remove leading dots
    sanitized = sanitized.lstrip('.')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = f"file_{uuid.uuid4().hex[:8]}"
    
    return sanitized


def create_response_dict(
    success: bool = True,
    message: Optional[str] = None,
    data: Optional[Any] = None,
    pagination: Optional[PaginationInfo] = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a standardized response dictionary"""
    response = {
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    if pagination:
        response["pagination"] = pagination.model_dump()
    
    # Add any additional fields
    response.update(kwargs)
    
    return response


def validate_file_upload(
    filename: str, 
    file_size: int,
    allowed_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Validate file upload parameters"""
    errors = []
    
    # Check file type
    allowed_file_types = allowed_types or settings.allowed_file_types
    if not is_allowed_file_type(filename):
        errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_file_types)}")
    
    # Check file size
    if file_size > settings.max_file_size:
        max_size_formatted = format_file_size(settings.max_file_size)
        current_size_formatted = format_file_size(file_size)
        errors.append(f"File too large. Maximum size: {max_size_formatted}, current size: {current_size_formatted}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }