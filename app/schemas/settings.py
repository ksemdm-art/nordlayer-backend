from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from .base import BaseSchema, TimestampedSchema

class SiteSettingBase(BaseSchema):
    key: str
    value: Optional[str] = None
    value_type: str = "text"
    description: Optional[str] = None
    category: str = "general"
    is_public: bool = True

class SiteSettingCreate(SiteSettingBase):
    pass

class SiteSettingUpdate(BaseSchema):
    value: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None

class SiteSetting(TimestampedSchema, SiteSettingBase):
    pass

class PageContentBase(BaseSchema):
    page_key: str
    section_key: str
    content_type: str = "text"
    content: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: str = "0"
    is_active: bool = True

class PageContentCreate(PageContentBase):
    pass

class PageContentUpdate(BaseSchema):
    content: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[str] = None
    is_active: Optional[bool] = None

class PageContent(TimestampedSchema, PageContentBase):
    pass

# Response schemas for frontend
class PublicSettings(BaseModel):
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None

class PageData(BaseModel):
    page_key: str
    sections: List[PageContent] = []
    settings: Dict[str, Any] = {}