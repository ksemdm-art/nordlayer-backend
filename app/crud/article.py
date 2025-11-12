from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate

class CRUDArticle(CRUDBase[Article, ArticleCreate, ArticleUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Article]:
        """Get article by slug."""
        return db.query(Article).filter(Article.slug == slug).first()

    def get_published(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Article]:
        """Get published articles."""
        return (
            db.query(Article)
            .filter(Article.is_published == True)
            .order_by(Article.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[Article]:
        """Get articles by category."""
        return (
            db.query(Article)
            .filter(Article.category == category, Article.is_published == True)
            .order_by(Article.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_title(self, db: Session, *, title: str, skip: int = 0, limit: int = 100) -> List[Article]:
        """Search articles by title."""
        return (
            db.query(Article)
            .filter(Article.title.contains(title), Article.is_published == True)
            .order_by(Article.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_content(self, db: Session, *, content: str, skip: int = 0, limit: int = 100) -> List[Article]:
        """Search articles by content."""
        return (
            db.query(Article)
            .filter(Article.content.contains(content), Article.is_published == True)
            .order_by(Article.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def publish(self, db: Session, *, article_id: int) -> Optional[Article]:
        """Publish an article."""
        from datetime import datetime
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            article.is_published = True
            if not article.published_at:
                article.published_at = datetime.utcnow()
            db.commit()
            db.refresh(article)
        return article

    def unpublish(self, db: Session, *, article_id: int) -> Optional[Article]:
        """Unpublish an article."""
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            article.is_published = False
            db.commit()
            db.refresh(article)
        return article

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ):
        """Get multiple articles with optional filtering."""
        query = db.query(self.model)
        
        if status_filter:
            if status_filter == "published":
                query = query.filter(self.model.status == "published")
            elif status_filter == "draft":
                query = query.filter(self.model.status == "draft")
        
        if category_filter:
            query = query.filter(self.model.category == category_filter)
        
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()

    def increment_views(self, db: Session, *, article_id: int) -> Optional[Article]:
        """Increment article views count."""
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            if not hasattr(article, 'views') or article.views is None:
                article.views = 1
            else:
                article.views += 1
            db.commit()
            db.refresh(article)
        return article

article = CRUDArticle(Article)