from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin_user
from app.crud.settings import site_setting, page_content
from app.schemas.settings import (
    SiteSetting, SiteSettingCreate, SiteSettingUpdate,
    PageContent, PageContentCreate, PageContentUpdate,
    PublicSettings, PageData
)
from app.schemas.base import APIResponse

router = APIRouter()

# Public endpoints (no auth required)
@router.get("/settings/public", response_model=APIResponse)
async def get_public_settings(db: Session = Depends(get_db)):
    """Get public site settings for frontend."""
    settings_dict = site_setting.get_settings_dict(db, public_only=True)
    
    return APIResponse(
        success=True,
        message="Public settings retrieved successfully",
        data=settings_dict
    )

@router.get("/pages/{page_key}", response_model=APIResponse)
async def get_page_content(
    page_key: str,
    db: Session = Depends(get_db)
):
    """Get content for a specific page."""
    sections = page_content.get_by_page(db, page_key=page_key)
    page_settings = site_setting.get_settings_dict(db, category=page_key, public_only=True)
    
    page_data = PageData(
        page_key=page_key,
        sections=sections,
        settings=page_settings
    )
    
    return APIResponse(
        success=True,
        message=f"Page content for '{page_key}' retrieved successfully",
        data=page_data
    )

# Admin endpoints (auth required)
@router.get("/admin/settings", response_model=APIResponse)
async def get_all_settings(
    category: str = None,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all settings (admin only)."""
    if category:
        settings = site_setting.get_by_category(db, category=category)
    else:
        settings = site_setting.get_multi(db, limit=1000)
    
    return APIResponse(
        success=True,
        message="Settings retrieved successfully",
        data=settings
    )

@router.post("/admin/settings", response_model=APIResponse)
async def create_setting(
    setting_data: SiteSettingCreate,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new setting (admin only)."""
    # Check if setting already exists
    existing = site_setting.get_by_key(db, key=setting_data.key)
    if existing:
        raise HTTPException(status_code=400, detail="Setting with this key already exists")
    
    setting = site_setting.create(db, obj_in=setting_data)
    
    return APIResponse(
        success=True,
        message="Setting created successfully",
        data=setting
    )

@router.put("/admin/settings/{setting_key}", response_model=APIResponse)
async def update_setting(
    setting_key: str,
    setting_data: SiteSettingUpdate,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update setting (admin only)."""
    setting = site_setting.get_by_key(db, key=setting_key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    updated_setting = site_setting.update(db, db_obj=setting, obj_in=setting_data)
    
    return APIResponse(
        success=True,
        message="Setting updated successfully",
        data=updated_setting
    )

@router.get("/admin/pages", response_model=APIResponse)
async def get_available_pages(
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get list of available pages (admin only)."""
    pages = page_content.get_available_pages(db)
    
    return APIResponse(
        success=True,
        message="Available pages retrieved successfully",
        data=pages
    )

@router.get("/admin/pages/{page_key}/content", response_model=APIResponse)
async def get_page_content_admin(
    page_key: str,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get page content for editing (admin only)."""
    sections = page_content.get_by_page(db, page_key=page_key, active_only=False)
    
    return APIResponse(
        success=True,
        message=f"Page content for '{page_key}' retrieved successfully",
        data=sections
    )

@router.post("/admin/pages/{page_key}/content", response_model=APIResponse)
async def create_page_content(
    page_key: str,
    content_data: PageContentCreate,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create page content (admin only)."""
    # Ensure page_key matches
    content_data.page_key = page_key
    
    # Check if content already exists
    existing = page_content.get_by_page_and_section(
        db, page_key=page_key, section_key=content_data.section_key
    )
    if existing:
        raise HTTPException(status_code=400, detail="Content for this section already exists")
    
    content = page_content.create(db, obj_in=content_data)
    
    return APIResponse(
        success=True,
        message="Page content created successfully",
        data=content
    )

@router.put("/admin/pages/{page_key}/content/{content_id}", response_model=APIResponse)
async def update_page_content(
    page_key: str,
    content_id: int,
    content_data: PageContentUpdate,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update page content (admin only)."""
    content = page_content.get(db, id=content_id)
    if not content or content.page_key != page_key:
        raise HTTPException(status_code=404, detail="Content not found")
    
    updated_content = page_content.update(db, db_obj=content, obj_in=content_data)
    
    return APIResponse(
        success=True,
        message="Page content updated successfully",
        data=updated_content
    )

@router.delete("/admin/pages/{page_key}/content/{content_id}", response_model=APIResponse)
async def delete_page_content(
    page_key: str,
    content_id: int,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete page content (admin only)."""
    content = page_content.get(db, id=content_id)
    if not content or content.page_key != page_key:
        raise HTTPException(status_code=404, detail="Content not found")
    
    page_content.remove(db, id=content_id)
    
    return APIResponse(
        success=True,
        message="Page content deleted successfully",
        data={"deleted_id": content_id}
    )