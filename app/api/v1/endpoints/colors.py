from typing import Any, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.deps import get_db, get_current_admin_user
from app.models.color import ColorType
from app.schemas.color import (
    Color, ColorCreate, ColorUpdate, 
    SolidColorResponse, GradientColorResponse, MetallicColorResponse
)

router = APIRouter()


def serialize_color(color) -> dict:
    """Helper function to serialize color object to dictionary"""
    color_data = {
        "id": color.id,
        "name": color.name,
        "type": color.type.value,
        "is_active": color.is_active,
        "is_new": color.is_new,
        "sort_order": color.sort_order,
        "price_modifier": color.price_modifier,
        "created_at": color.created_at.isoformat() if color.created_at else None,
        "updated_at": color.updated_at.isoformat() if color.updated_at else None
    }
    
    # Add type-specific fields
    if color.type == ColorType.SOLID:
        color_data["hex_code"] = color.hex_code
    elif color.type == ColorType.GRADIENT:
        color_data["gradient_colors"] = color.gradient_colors
        color_data["gradient_direction"] = color.gradient_direction
    elif color.type == ColorType.METALLIC:
        color_data["metallic_base"] = color.metallic_base
        color_data["metallic_intensity"] = color.metallic_intensity
    
    return color_data


@router.get("/types", response_model=Any)
def get_color_types() -> Any:
    """
    Get available color types.
    """
    return {
        "success": True, 
        "data": [
            {"value": ColorType.SOLID.value, "label": "Solid Color"},
            {"value": ColorType.GRADIENT.value, "label": "Gradient"},
            {"value": ColorType.METALLIC.value, "label": "Metallic"}
        ]
    }


@router.get("/", response_model=Any)
def read_colors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    color_type: ColorType = Query(None, description="Filter by color type"),
    include_inactive: bool = Query(False, description="Include inactive colors"),
) -> Any:
    """
    Retrieve colors with optional filtering by type.
    """
    if color_type:
        if include_inactive:
            # Get all colors of specific type (including inactive)
            colors = db.query(crud.color.model).filter(crud.color.model.type == color_type).order_by(crud.color.model.sort_order, crud.color.model.name).all()
        else:
            colors = crud.color.get_colors_by_type(db, color_type=color_type)
    else:
        if include_inactive:
            # Get all colors (including inactive) for admin
            colors = crud.color.get_all_colors_for_admin(db, skip=skip, limit=limit)
        else:
            colors = crud.color.get_active_colors(db)
    
    # Convert to dictionaries for serialization with enhanced fields
    colors_data = [serialize_color(color) for color in colors]
    
    return {"success": True, "data": colors_data}


@router.post("/", response_model=Any)
def create_color(
    *,
    db: Session = Depends(get_db),
    color_in: ColorCreate,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new color with support for all color types.
    """
    # Check if color with same name already exists
    existing_name = crud.color.get_by_name(db, name=color_in.name)
    if existing_name:
        raise HTTPException(
            status_code=400,
            detail="Color with this name already exists"
        )
    
    # For solid colors, check hex code uniqueness
    if color_in.type == ColorType.SOLID and color_in.hex_code:
        existing_hex = crud.color.get_by_hex_code(db, hex_code=color_in.hex_code)
        if existing_hex:
            raise HTTPException(
                status_code=400,
                detail="Color with this hex code already exists"
            )
    
    # Create color (validation is handled in CRUD layer)
    color = crud.color.create(db=db, obj_in=color_in)
    
    return {"success": True, "data": serialize_color(color), "message": "Color created successfully"}


@router.put("/{id}", response_model=Any)
def update_color(
    *,
    db: Session = Depends(get_db),
    id: int,
    color_in: ColorUpdate,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Update color with support for all color types.
    """
    color = crud.color.get(db=db, id=id)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    
    # Check for conflicts if updating name
    if color_in.name and color_in.name != color.name:
        existing_name = crud.color.get_by_name(db, name=color_in.name)
        if existing_name:
            raise HTTPException(
                status_code=400,
                detail="Color with this name already exists"
            )
    
    # For solid colors, check hex code uniqueness
    if (color_in.hex_code and 
        (color_in.type == ColorType.SOLID or color.type == ColorType.SOLID) and
        color_in.hex_code != color.hex_code):
        existing_hex = crud.color.get_by_hex_code(db, hex_code=color_in.hex_code)
        if existing_hex:
            raise HTTPException(
                status_code=400,
                detail="Color with this hex code already exists"
            )
    
    # Update color (validation is handled in CRUD layer)
    updated_color = crud.color.update(db=db, db_obj=color, obj_in=color_in)
    
    return {"success": True, "data": serialize_color(updated_color), "message": "Color updated successfully"}


@router.get("/{id}", response_model=Any)
def read_color(
    *,
    db: Session = Depends(get_db),
    id: int,
) -> Any:
    """
    Get color by ID.
    """
    color = crud.color.get(db=db, id=id)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    
    return {"success": True, "data": serialize_color(color)}


@router.delete("/{id}", response_model=Any)
def delete_color(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Delete color.
    """
    color = crud.color.get(db=db, id=id)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    
    color = crud.color.remove(db=db, id=id)
    return {"success": True, "message": "Color deleted successfully"}


@router.get("/by-type/{color_type}", response_model=Any)
def get_colors_by_type(
    *,
    db: Session = Depends(get_db),
    color_type: str,
) -> Any:
    """
    Get colors filtered by specific type.
    """
    # Validate color type
    try:
        color_type_enum = ColorType(color_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid color type. Must be one of: {[t.value for t in ColorType]}"
        )
    
    colors = crud.color.get_colors_by_type(db, color_type=color_type_enum)
    
    # Convert to dictionaries for serialization with enhanced fields
    colors_data = [serialize_color(color) for color in colors]
    
    return {"success": True, "data": colors_data}


@router.patch("/{id}/toggle-active", response_model=Any)
def toggle_color_active_status(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Toggle active status of a color (admin only).
    """
    color = crud.color.get(db=db, id=id)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    
    # Toggle the active status
    color_update = schemas.ColorUpdate(is_active=not color.is_active)
    updated_color = crud.color.update(db=db, db_obj=color, obj_in=color_update)
    
    status = "активирован" if updated_color.is_active else "деактивирован"
    return {
        "success": True, 
        "data": serialize_color(updated_color), 
        "message": f"Цвет '{updated_color.name}' {status}"
    }


@router.patch("/{id}/toggle-new", response_model=Any)
def toggle_color_new_status(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: models.User = Depends(get_current_admin_user),
) -> Any:
    """
    Toggle new status of a color (admin only).
    """
    color = crud.color.get(db=db, id=id)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    
    # Toggle the new status
    color_update = schemas.ColorUpdate(is_new=not color.is_new)
    updated_color = crud.color.update(db=db, db_obj=color, obj_in=color_update)
    
    status = "отмечен как новинка" if updated_color.is_new else "убран из новинок"
    return {
        "success": True, 
        "data": serialize_color(updated_color), 
        "message": f"Цвет '{updated_color.name}' {status}"
    }