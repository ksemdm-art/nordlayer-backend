from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import category
from app.schemas.category import Category, CategoryCreate, CategoryUpdate
from app.schemas.response import DataResponse, ListResponse

router = APIRouter()

@router.get("/", response_model=ListResponse[Category])
async def get_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[str] = Query(None, description="Filter by category type (article, project, service)"),
    active_only: bool = Query(True, description="Show only active categories")
):
    """Get list of categories with optional filtering."""
    try:
        if type:
            categories = category.get_by_type(db, type=type, skip=skip, limit=limit)
        elif active_only:
            categories = category.get_active(db, skip=skip, limit=limit)
        else:
            categories = category.get_multi(db, skip=skip, limit=limit)
        
        return ListResponse(
            success=True,
            data=categories,
            message=f"Retrieved {len(categories)} categories"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{category_id}", response_model=DataResponse[Category])
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID."""
    db_category = category.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return DataResponse(
        success=True,
        data=db_category,
        message="Category retrieved successfully"
    )

@router.get("/slug/{slug}", response_model=DataResponse[Category])
async def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get category by slug."""
    db_category = category.get_by_slug(db, slug=slug)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return DataResponse(
        success=True,
        data=db_category,
        message="Category retrieved successfully"
    )

@router.post("/", response_model=DataResponse[Category])
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new category."""
    # Check if category with same slug already exists
    existing_category = category.get_by_slug(db, slug=category_data.slug)
    if existing_category:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    try:
        db_category = category.create(db, obj_in=category_data)
        return DataResponse(
            success=True,
            data=db_category,
            message="Category created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{category_id}", response_model=DataResponse[Category])
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a category."""
    db_category = category.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if slug is being updated and if it conflicts
    if category_data.slug and category_data.slug != db_category.slug:
        existing_category = category.get_by_slug(db, slug=category_data.slug)
        if existing_category:
            raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    try:
        updated_category = category.update(db, db_obj=db_category, obj_in=category_data)
        return DataResponse(
            success=True,
            data=updated_category,
            message="Category updated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{category_id}", response_model=DataResponse[Category])
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Deactivate a category (soft delete)."""
    db_category = category.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    try:
        deactivated_category = category.deactivate(db, id=category_id)
        return DataResponse(
            success=True,
            data=deactivated_category,
            message="Category deactivated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{category_id}/activate", response_model=DataResponse[Category])
async def activate_category(category_id: int, db: Session = Depends(get_db)):
    """Activate a category."""
    db_category = category.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    try:
        activated_category = category.activate(db, id=category_id)
        return DataResponse(
            success=True,
            data=activated_category,
            message="Category activated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/", response_model=ListResponse[Category])
async def search_categories(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Search categories by name."""
    try:
        categories = category.search_by_name(db, name=q, skip=skip, limit=limit)
        return ListResponse(
            success=True,
            data=categories,
            message=f"Found {len(categories)} categories matching '{q}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))