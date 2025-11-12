from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user
from app.models.project import ComplexityLevel
from app.core.utils import (
    calculate_pagination, 
    get_skip_limit, 
    create_response_dict,
    validate_file_upload,
    generate_unique_filename,
    ensure_upload_directory
)
from app.core.exceptions import NotFoundError, FileUploadError
from app.schemas.project import Project, ProjectCreate, ProjectUpdate, ProjectSummary
from app.schemas.response import PaginatedResponse, DataResponse
from app.services.project import project_service
from app.services.s3_manager import s3_manager
from app.services.cache_service import cache_service, CacheKeys
from app.services.model_optimization import model_optimization_service
from app.core.config import settings
from app.core.performance import (
    performance_tracker, 
    cache_manager, 
    DatabaseOptimizer, 
    ResponseOptimizer
)
import os
import shutil
from pathlib import Path

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectSummary])
@performance_tracker
@cache_manager.cache_response("projects_list", ttl=900)
async def get_projects(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    complexity_levels: Optional[List[ComplexityLevel]] = Query(None, description="Filter by complexity levels"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    min_hours: Optional[int] = Query(None, ge=0, description="Minimum duration in hours"),
    max_hours: Optional[int] = Query(None, ge=0, description="Maximum duration in hours"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of projects with optional filtering and search
    
    - **page**: Page number (starts from 1)
    - **per_page**: Number of items per page (max 100)
    - **category**: Filter projects by category
    - **is_featured**: Filter by featured status (true/false)
    - **search**: Search term for title and description
    - **complexity_levels**: Filter by complexity levels
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **min_hours**: Minimum duration in hours
    - **max_hours**: Maximum duration in hours
    """
    # Optimize pagination parameters
    skip, limit = DatabaseOptimizer.optimize_query_params(page, per_page, max_limit=100)
    
    # Build optimized filters
    filters = DatabaseOptimizer.build_filters({
        'category': category,
        'is_featured': is_featured,
        'search_like': search,
        'complexity_levels_in': complexity_levels,
        'min_price': min_price,
        'max_price': max_price,
        'min_hours': min_hours,
        'max_hours': max_hours
    })
    
    # Get projects with optimized filters
    projects = project_service.get_projects_with_filters(
        db,
        skip=skip,
        limit=limit,
        **filters
    )
    
    # Get total count for pagination (optimized)
    total = project_service.count_projects_with_filters(db, **filters)
    
    # Create optimized paginated response
    return ResponseOptimizer.paginate_response(
        data=projects,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/featured", response_model=DataResponse[List[ProjectSummary]])
async def get_featured_projects(
    limit: int = Query(10, ge=1, le=50, description="Number of featured projects to return"),
    db: Session = Depends(get_db)
):
    """Get featured projects"""
    projects = project_service.get_featured_projects(db, limit=limit)
    
    return DataResponse(
        data=projects,
        message=f"Retrieved {len(projects)} featured projects"
    )


@router.get("/categories", response_model=DataResponse[List[str]])
async def get_project_categories(db: Session = Depends(get_db)):
    """Get list of available project categories"""
    categories = project_service.get_available_categories(db)
    
    return DataResponse(
        data=categories,
        message="Project categories retrieved successfully"
    )


@router.get("/complexity-levels", response_model=DataResponse[List[str]])
async def get_complexity_levels():
    """Get list of available complexity levels"""
    complexity_levels = [level.value for level in ComplexityLevel]
    
    return DataResponse(
        data=complexity_levels,
        message="Complexity levels retrieved successfully"
    )


@router.get("/{project_id}", response_model=DataResponse[Project])
@performance_tracker
@cache_manager.cache_response("project_detail", ttl=3600)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific project
    
    - **project_id**: ID of the project to retrieve
    """
    try:
        # Try to get from cache first
        cache_key = CacheKeys.project_detail(project_id)
        cached_project = await cache_service.get(cache_key)
        if cached_project:
            return DataResponse(
                data=cached_project,
                message="Project retrieved successfully"
            )
        
        # Get from database
        project = project_service.get_project_with_images(db, project_id)
        
        # Cache the project for 1 hour
        project_dict = project.dict() if hasattr(project, 'dict') else project.__dict__
        await cache_service.set(cache_key, project_dict, 3600)
        
        return DataResponse(
            data=project,
            message="Project retrieved successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/stl")
async def get_project_stl_file(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Download STL file for a project
    
    - **project_id**: ID of the project
    """
    try:
        project = project_service.get_or_404(db, project_id)
        
        if not project.stl_file:
            raise HTTPException(
                status_code=404, 
                detail="STL file not available for this project"
            )
        
        file_path = Path(project.stl_file)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="STL file not found on server"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=f"{project.title}.stl",
            media_type="application/octet-stream"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/stl/optimized")
async def get_optimized_project_stl(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get optimized STL file for a project
    
    - **project_id**: ID of the project
    """
    try:
        project = project_service.get_or_404(db, project_id)
        
        if not project.stl_file:
            raise HTTPException(
                status_code=404, 
                detail="STL file not available for this project"
            )
        
        # Get optimized model URL
        optimized_url = await model_optimization_service.get_optimized_model_url(project.stl_file)
        
        if not optimized_url:
            # Fallback to original file
            file_path = Path(project.stl_file)
            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="STL file not found on server"
                )
            
            return FileResponse(
                path=str(file_path),
                filename=f"{project.title}.stl",
                media_type="application/octet-stream"
            )
        
        # Return optimized file
        optimized_path = Path(optimized_url.replace('/uploads/', 'uploads/'))
        
        if not optimized_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Optimized file not found"
            )
        
        # Determine content type based on file extension
        if optimized_path.suffix == '.gz':
            media_type = "application/gzip"
            filename = f"{project.title}_optimized.stl.gz"
        else:
            media_type = "application/octet-stream"
            filename = f"{project.title}_optimized{optimized_path.suffix}"
        
        return FileResponse(
            path=str(optimized_path),
            filename=filename,
            media_type=media_type
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/model-info")
async def get_project_model_info(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get information about project's 3D model
    
    - **project_id**: ID of the project
    """
    try:
        project = project_service.get_or_404(db, project_id)
        
        if not project.stl_file:
            raise HTTPException(
                status_code=404, 
                detail="STL file not available for this project"
            )
        
        # Get model information
        model_info = await model_optimization_service.get_model_info(project.stl_file)
        
        return {
            "success": True,
            "data": model_info,
            "message": "Model information retrieved successfully"
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=DataResponse[Project])
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Create a new project (Admin only)
    
    - **project_data**: Project information
    """
    project = project_service.create(db, obj_in=project_data)
    
    return DataResponse(
        data=project,
        message="Project created successfully"
    )


@router.put("/{project_id}", response_model=DataResponse[Project])
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update an existing project (Admin only)
    
    - **project_id**: ID of the project to update
    - **project_data**: Updated project information
    """
    try:
        project = project_service.get_or_404(db, project_id)
        updated_project = project_service.update(db, db_obj=project, obj_in=project_data)
        
        return DataResponse(
            data=updated_project,
            message="Project updated successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Delete a project (Admin only)
    
    - **project_id**: ID of the project to delete
    """
    try:
        project_service.delete(db, id=project_id)
        
        return create_response_dict(
            message="Project deleted successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/stl", response_model=DataResponse[Project])
async def upload_project_stl(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Upload STL file for a project (Admin only)
    
    - **project_id**: ID of the project
    - **file**: STL file to upload
    """
    try:
        # Validate file
        if not file.filename:
            raise FileUploadError("No file provided")
        
        # Check file type (should be STL)
        if not file.filename.lower().endswith('.stl'):
            raise FileUploadError("Only STL files are allowed")
        
        file_url = None
        
        if settings.use_s3 and s3_manager:
            # Upload to S3
            folder = f"uploads/projects/{project_id}/models"
            file_url = await s3_manager.upload_file(file, folder, validate=True)
            
            # Update project with S3 file URL
            project = project_service.update_project_stl_file(
                db, project_id, file_url
            )
        else:
            # Fallback to local storage
            # Validate file size (this is approximate, actual size check happens during read)
            validation = validate_file_upload(file.filename, 0)  # Size will be checked during read
            if not validation["valid"]:
                raise FileUploadError("; ".join(validation["errors"]))
            
            # Ensure upload directory exists
            upload_dir = ensure_upload_directory()
            stl_dir = Path(upload_dir) / "stl"
            stl_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            unique_filename = generate_unique_filename(file.filename)
            file_path = stl_dir / unique_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                
                # Check actual file size
                if len(content) > 50 * 1024 * 1024:  # 50MB limit
                    raise FileUploadError("File too large. Maximum size is 50MB")
                
                buffer.write(content)
            
            # Update project with local file path
            project = project_service.update_project_stl_file(
                db, project_id, str(file_path)
            )
        
        return DataResponse(
            data=project,
            message="STL file uploaded successfully"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up local file if it was created and upload failed
        if not settings.use_s3 and 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="File upload failed")


@router.post("/{project_id}/images")
async def upload_project_image(
    project_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = None,
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Upload an image for a project (Admin only)
    
    - **project_id**: ID of the project
    - **file**: Image file to upload
    - **alt_text**: Alternative text for the image
    - **is_primary**: Whether this should be the primary image
    """
    try:
        # Validate file
        if not file.filename:
            raise FileUploadError("No file provided")
        
        # Check file type (should be image)
        allowed_image_types = ['.jpg', '.jpeg', '.png']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_image_types):
            raise FileUploadError("Only JPG, JPEG, and PNG files are allowed")
        
        file_url = None
        
        if settings.use_s3 and s3_manager:
            # Upload to S3
            folder = f"uploads/projects/{project_id}/images"
            file_url = await s3_manager.upload_file(file, folder, validate=True)
            
            # Add image to project with S3 URL
            project_image = project_service.add_image_to_project(
                db, project_id, file_url, alt_text, is_primary
            )
        else:
            # Fallback to local storage
            # Ensure upload directory exists
            upload_dir = ensure_upload_directory()
            images_dir = Path(upload_dir) / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            unique_filename = generate_unique_filename(file.filename)
            file_path = images_dir / unique_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                
                # Check file size
                if len(content) > 10 * 1024 * 1024:  # 10MB limit for images
                    raise FileUploadError("Image too large. Maximum size is 10MB")
                
                buffer.write(content)
            
            # Add image to project with local file path
            project_image = project_service.add_image_to_project(
                db, project_id, str(file_path), alt_text, is_primary
            )
        
        return create_response_dict(
            message="Image uploaded successfully",
            data={
                "image_id": project_image.id,
                "image_path": project_image.image_path,
                "is_primary": project_image.is_primary
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up file if it was created
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="Image upload failed")