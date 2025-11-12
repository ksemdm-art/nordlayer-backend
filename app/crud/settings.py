from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.settings import SiteSetting, PageContent
from app.schemas.settings import (
    SiteSettingCreate, SiteSettingUpdate,
    PageContentCreate, PageContentUpdate
)

class CRUDSiteSetting(CRUDBase[SiteSetting, SiteSettingCreate, SiteSettingUpdate]):
    def get_by_key(self, db: Session, *, key: str) -> Optional[SiteSetting]:
        """Get setting by key."""
        return db.query(SiteSetting).filter(SiteSetting.key == key).first()

    def get_by_category(self, db: Session, *, category: str) -> List[SiteSetting]:
        """Get settings by category."""
        return db.query(SiteSetting).filter(SiteSetting.category == category).all()

    def get_public_settings(self, db: Session) -> List[SiteSetting]:
        """Get all public settings."""
        return db.query(SiteSetting).filter(SiteSetting.is_public == True).all()

    def set_setting(self, db: Session, *, key: str, value: str, **kwargs) -> SiteSetting:
        """Set or update a setting."""
        setting = self.get_by_key(db, key=key)
        if setting:
            setting.value = value
            for field, val in kwargs.items():
                if hasattr(setting, field):
                    setattr(setting, field, val)
            db.add(setting)
        else:
            setting_data = SiteSettingCreate(key=key, value=value, **kwargs)
            setting = self.create(db, obj_in=setting_data)
        
        db.commit()
        db.refresh(setting)
        return setting

    def get_settings_dict(self, db: Session, *, category: Optional[str] = None, public_only: bool = False) -> Dict[str, Any]:
        """Get settings as a dictionary."""
        query = db.query(SiteSetting)
        
        if category:
            query = query.filter(SiteSetting.category == category)
        if public_only:
            query = query.filter(SiteSetting.is_public == True)
        
        settings = query.all()
        result = {}
        
        for setting in settings:
            if setting.value_type == "json":
                import json
                try:
                    result[setting.key] = json.loads(setting.value or "{}")
                except:
                    result[setting.key] = {}
            elif setting.value_type == "boolean":
                result[setting.key] = setting.value.lower() in ("true", "1", "yes") if setting.value else False
            elif setting.value_type == "number":
                try:
                    result[setting.key] = float(setting.value) if setting.value else 0
                except:
                    result[setting.key] = 0
            else:
                result[setting.key] = setting.value
        
        return result

class CRUDPageContent(CRUDBase[PageContent, PageContentCreate, PageContentUpdate]):
    def get_by_page_and_section(self, db: Session, *, page_key: str, section_key: str) -> Optional[PageContent]:
        """Get content by page and section key."""
        return db.query(PageContent).filter(
            PageContent.page_key == page_key,
            PageContent.section_key == section_key
        ).first()

    def get_by_page(self, db: Session, *, page_key: str, active_only: bool = True) -> List[PageContent]:
        """Get all content for a page."""
        query = db.query(PageContent).filter(PageContent.page_key == page_key)
        if active_only:
            query = query.filter(PageContent.is_active == True)
        return query.order_by(PageContent.order_index, PageContent.id).all()

    def set_content(self, db: Session, *, page_key: str, section_key: str, **kwargs) -> PageContent:
        """Set or update page content."""
        content = self.get_by_page_and_section(db, page_key=page_key, section_key=section_key)
        if content:
            for field, value in kwargs.items():
                if hasattr(content, field):
                    setattr(content, field, value)
            db.add(content)
        else:
            content_data = PageContentCreate(
                page_key=page_key,
                section_key=section_key,
                **kwargs
            )
            content = self.create(db, obj_in=content_data)
        
        db.commit()
        db.refresh(content)
        return content

    def get_available_pages(self, db: Session) -> List[str]:
        """Get list of available page keys."""
        pages = db.query(PageContent.page_key).distinct().all()
        return [page[0] for page in pages]

site_setting = CRUDSiteSetting(SiteSetting)
page_content = CRUDPageContent(PageContent)