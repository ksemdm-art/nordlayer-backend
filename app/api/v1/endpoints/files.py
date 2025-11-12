from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path
from typing import Optional, List
from app.core.config import settings
from app.services.s3_manager import s3_manager
from app.services.file_service import file_service

router = APIRouter()

# Создаем директорию для загрузок если её нет (fallback для локального хранения)
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = Query("temp", description="Folder path for the file")
):
    """Upload file with validation and preview generation"""
    try:
        # Use S3 if enabled, otherwise use enhanced local storage
        if settings.use_s3 and s3_manager:
            # Upload to S3
            file_url = await s3_manager.upload_file(file, folder)
            file_size = file.size if hasattr(file, 'size') else len(await file.read())
            await file.seek(0)  # Reset file pointer
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "File uploaded successfully to S3",
                    "data": {
                        "url": file_url,
                        "filename": file.filename,
                        "size": file_size,
                        "storage": "s3"
                    }
                }
            )
        else:
            # Use enhanced local storage with file service
            file_info = await file_service.save_file(file, folder)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "File uploaded successfully",
                    "data": {
                        **file_info,
                        "storage": "local"
                    }
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@router.delete("/delete")
async def delete_file(file_url: str):
    """Delete file from S3 or local storage"""
    try:
        if settings.use_s3 and s3_manager and settings.s3_endpoint_url in file_url:
            # Delete from S3
            success = s3_manager.delete_file(file_url)
            if success:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "File deleted successfully from S3"
                    }
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="File not found or could not be deleted"
                )
        else:
            # Delete from local storage using file service
            success = file_service.delete_file(file_url)
            
            if success:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "File deleted successfully from local storage"
                    }
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )

@router.get("/list")
async def list_files(folder: Optional[str] = Query("", description="Folder to list files from")):
    """List files from S3 or local storage with enhanced information"""
    try:
        if settings.use_s3 and s3_manager:
            # List from S3
            files = s3_manager.list_files(folder)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Files listed successfully from S3",
                    "data": {
                        "files": files,
                        "storage": "s3"
                    }
                }
            )
        else:
            # List from local storage using file service
            files = file_service.list_files(folder)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Files listed successfully from local storage",
                    "data": {
                        "files": files,
                        "storage": "local"
                    }
                }
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )

@router.post("/upload-order-files/{order_id}")
async def upload_order_files(
    order_id: int,
    files: List[UploadFile] = File(...),
    file_type: str = Query("models", description="Type of files: 'models' or 'images'")
):
    """Upload multiple files for a specific order with validation and preview generation"""
    try:
        if settings.use_s3 and s3_manager:
            # Upload to S3
            uploaded_files = []
            folder = f"uploads/orders/{order_id}/{file_type}"
            
            for file in files:
                file_url = await s3_manager.upload_file(file, folder)
                file_size = file.size if hasattr(file, 'size') else len(await file.read())
                await file.seek(0)
                
                uploaded_files.append({
                    "url": file_url,
                    "filename": file.filename,
                    "size": file_size,
                    "storage": "s3"
                })
        else:
            # Use enhanced local storage with file service
            uploaded_files = await file_service.save_order_files(order_id, files, file_type)
            
            # Add storage info to each file
            for file_info in uploaded_files:
                file_info["storage"] = "local"
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Successfully uploaded {len(uploaded_files)} files for order {order_id}",
                "data": {
                    "files": uploaded_files,
                    "order_id": order_id,
                    "file_type": file_type
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading order files: {str(e)}"
        )

@router.get("/presigned-url")
async def get_presigned_url(
    key: str = Query(..., description="S3 object key"),
    expiration: int = Query(3600, description="URL expiration in seconds"),
    method: str = Query("get_object", description="S3 method (get_object or put_object)")
):
    """Generate presigned URL for secure file access (S3 only)"""
    try:
        if not settings.use_s3 or not s3_manager:
            raise HTTPException(
                status_code=400,
                detail="Presigned URLs are only available with S3 storage"
            )
        
        presigned_url = s3_manager.generate_presigned_url(key, expiration, method)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Presigned URL generated successfully",
                "data": {
                    "url": presigned_url,
                    "key": key,
                    "expiration": expiration
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating presigned URL: {str(e)}"
        )

@router.get("/info")
async def get_file_info(file_url: str = Query(..., description="File URL to get info for")):
    """Get detailed information about a file"""
    try:
        if settings.use_s3 and s3_manager and settings.s3_endpoint_url in file_url:
            # Get info from S3 (would need to implement in s3_manager)
            raise HTTPException(
                status_code=501,
                detail="File info for S3 files not implemented yet"
            )
        else:
            # Get info from local storage
            file_info = file_service.get_file_info(file_url)
            
            if file_info:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "File info retrieved successfully",
                        "data": file_info
                    }
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting file info: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_files(
    background_tasks: BackgroundTasks,
    max_age_days: int = Query(7, description="Maximum age in days for temporary files")
):
    """Clean up old temporary files"""
    try:
        # Run cleanup in background
        background_tasks.add_task(file_service.cleanup_old_files, max_age_days)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"File cleanup started for files older than {max_age_days} days"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting file cleanup: {str(e)}"
        )


@router.get("/validate")
async def validate_file_endpoint(
    filename: str = Query(..., description="Filename to validate"),
    size: Optional[int] = Query(None, description="File size in bytes")
):
    """Validate file without uploading it"""
    try:
        # Create a mock UploadFile for validation
        class MockUploadFile:
            def __init__(self, filename: str, size: Optional[int] = None):
                self.filename = filename
                self.size = size
        
        mock_file = MockUploadFile(filename, size)
        validation_result = file_service.validate_file(mock_file)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "File validation completed",
                "data": validation_result
            }
        )
        
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "message": e.detail,
                "data": {
                    "filename": filename,
                    "is_valid": False
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating file: {str(e)}"
        )


@router.post("/cleanup/orphaned")
async def cleanup_orphaned_files(background_tasks: BackgroundTasks):
    """Clean up orphaned files that are not referenced in database"""
    try:
        from app.services.file_cleanup_service import file_cleanup_service
        
        # Run cleanup in background
        background_tasks.add_task(file_cleanup_service.cleanup_orphaned_files)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Orphaned file cleanup started"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting orphaned file cleanup: {str(e)}"
        )


@router.post("/cleanup/full")
async def full_cleanup(background_tasks: BackgroundTasks):
    """Perform full file cleanup including orphaned files, old temp files, and failed uploads"""
    try:
        from app.services.file_cleanup_service import file_cleanup_service
        
        # Run full cleanup in background
        background_tasks.add_task(file_cleanup_service.full_cleanup)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Full file cleanup started"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting full file cleanup: {str(e)}"
        )


@router.get("/stats")
async def get_storage_stats():
    """Get storage usage statistics"""
    try:
        from app.services.file_cleanup_service import file_cleanup_service
        
        stats = await file_cleanup_service.get_storage_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Storage statistics retrieved successfully",
                "data": stats
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting storage statistics: {str(e)}"
        )