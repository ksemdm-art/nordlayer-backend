from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.content import Content, Page
from app.schemas.content import ContentCreate, ContentUpdate, PageCreate, PageUpdate

class CRUDContent(CRUDBase[Content, ContentCreate, ContentUpdate]):
    def get_by_key(self, db: Session, *, key: str) -> Optional[Content]:
        """Получить контент по ключу."""
        return db.query(Content).filter(Content.key == key, Content.is_active == True).first()

    def get_by_group(self, db: Session, *, group_name: str) -> List[Content]:
        """Получить весь контент группы."""
        return (
            db.query(Content)
            .filter(Content.group_name == group_name, Content.is_active == True)
            .order_by(Content.sort_order, Content.key)
            .all()
        )

    def get_by_keys(self, db: Session, *, keys: List[str]) -> List[Content]:
        """Получить контент по списку ключей."""
        return (
            db.query(Content)
            .filter(Content.key.in_(keys), Content.is_active == True)
            .all()
        )

    def get_all_groups(self, db: Session) -> List[str]:
        """Получить список всех групп."""
        result = db.query(Content.group_name).filter(Content.group_name.isnot(None)).distinct().all()
        return [row[0] for row in result if row[0]]

    def get_content_dict(self, db: Session, *, keys: List[str] = None, group_name: str = None) -> Dict[str, Any]:
        """Получить контент в виде словаря ключ-значение."""
        query = db.query(Content).filter(Content.is_active == True)
        
        if keys:
            query = query.filter(Content.key.in_(keys))
        elif group_name:
            query = query.filter(Content.group_name == group_name)
        
        contents = query.all()
        result = {}
        
        for content in contents:
            if content.content_type == "json" and content.json_content:
                result[content.key] = content.json_content
            else:
                result[content.key] = content.content
                
        return result

    def upsert_content(self, db: Session, *, key: str, content_data: ContentCreate) -> Content:
        """Создать или обновить контент по ключу."""
        existing = self.get_by_key(db, key=key)
        
        if existing:
            # Обновляем существующий
            update_data = content_data.model_dump(exclude_unset=True)
            return self.update(db, db_obj=existing, obj_in=update_data)
        else:
            # Создаем новый
            return self.create(db, obj_in=content_data)

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        group_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None
    ):
        """Получить множественный контент с фильтрацией."""
        query = db.query(self.model)
        
        if group_filter:
            query = query.filter(self.model.group_name == group_filter)
        
        if content_type_filter:
            query = query.filter(self.model.content_type == content_type_filter)
        
        return query.order_by(self.model.group_name, self.model.sort_order, self.model.key).offset(skip).limit(limit).all()

class CRUDPage(CRUDBase[Page, PageCreate, PageUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Page]:
        """Получить страницу по slug."""
        return db.query(Page).filter(Page.slug == slug, Page.is_active == True).first()

    def get_by_type(self, db: Session, *, page_type: str) -> List[Page]:
        """Получить страницы по типу."""
        return (
            db.query(Page)
            .filter(Page.page_type == page_type, Page.is_active == True)
            .all()
        )

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        page_type_filter: Optional[str] = None
    ):
        """Получить множественные страницы с фильтрацией."""
        query = db.query(self.model)
        
        if page_type_filter:
            query = query.filter(self.model.page_type == page_type_filter)
        
        return query.order_by(self.model.title).offset(skip).limit(limit).all()

content = CRUDContent(Content)
page = CRUDPage(Page)