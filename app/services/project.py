"""
Project service for handling project-related business logic
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.project import Project, ProjectImage, ComplexityLevel
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.base import BaseService
from app.core.exceptions import NotFoundError, ValidationError


class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    """Service for project operations"""
    
    def __init__(self):
        super().__init__(Project)
    
    def get_projects_with_filters(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        complexity_levels: Optional[List[ComplexityLevel]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_hours: Optional[int] = None,
        max_hours: Optional[int] = None
    ) -> List[Project]:
        """Get projects with filtering and search"""
        query = db.query(self.model)
        
        # Apply filters
        if category:
            query = query.filter(self.model.category == category)
        
        if is_featured is not None:
            query = query.filter(self.model.is_featured == is_featured)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    self.model.title.ilike(search_term),
                    self.model.description.ilike(search_term)
                )
            )
        
        # New pricing and complexity filters
        if complexity_levels:
            query = query.filter(self.model.complexity_level.in_(complexity_levels))
        
        if min_price is not None:
            query = query.filter(
                or_(
                    self.model.estimated_price >= min_price,
                    self.model.price_range_min >= min_price
                )
            )
        
        if max_price is not None:
            query = query.filter(
                or_(
                    self.model.estimated_price <= max_price,
                    self.model.price_range_max <= max_price
                )
            )
        
        if min_hours is not None:
            query = query.filter(self.model.estimated_duration_hours >= min_hours)
        
        if max_hours is not None:
            query = query.filter(self.model.estimated_duration_hours <= max_hours)
        
        # Order by featured first, then by creation date
        query = query.order_by(
            self.model.is_featured.desc(),
            self.model.created_at.desc()
        )
        
        return query.offset(skip).limit(limit).all()
    
    def count_projects_with_filters(
        self,
        db: Session,
        *,
        category: Optional[str] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        complexity_levels: Optional[List[ComplexityLevel]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_hours: Optional[int] = None,
        max_hours: Optional[int] = None
    ) -> int:
        """Count projects with filtering"""
        query = db.query(self.model)
        
        # Apply same filters as get_projects_with_filters
        if category:
            query = query.filter(self.model.category == category)
        
        if is_featured is not None:
            query = query.filter(self.model.is_featured == is_featured)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    self.model.title.ilike(search_term),
                    self.model.description.ilike(search_term)
                )
            )
        
        # New pricing and complexity filters
        if complexity_levels:
            query = query.filter(self.model.complexity_level.in_(complexity_levels))
        
        if min_price is not None:
            query = query.filter(
                or_(
                    self.model.estimated_price >= min_price,
                    self.model.price_range_min >= min_price
                )
            )
        
        if max_price is not None:
            query = query.filter(
                or_(
                    self.model.estimated_price <= max_price,
                    self.model.price_range_max <= max_price
                )
            )
        
        if min_hours is not None:
            query = query.filter(self.model.estimated_duration_hours >= min_hours)
        
        if max_hours is not None:
            query = query.filter(self.model.estimated_duration_hours <= max_hours)
        
        return query.count()
    
    def get_project_with_images(self, db: Session, project_id: int) -> Project:
        """Get project with all its images"""
        project = db.query(self.model).filter(
            self.model.id == project_id
        ).first()
        
        if not project:
            raise NotFoundError("Project", project_id)
        
        return project
    
    def get_featured_projects(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Project]:
        """Get featured projects"""
        return db.query(self.model).filter(
            self.model.is_featured == True
        ).order_by(
            self.model.created_at.desc()
        ).limit(limit).all()
    
    def get_projects_by_category(
        self, 
        db: Session, 
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get projects by category"""
        return db.query(self.model).filter(
            self.model.category == category
        ).order_by(
            self.model.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_available_categories(self, db: Session) -> List[str]:
        """Get list of available project categories"""
        categories = db.query(self.model.category).distinct().all()
        return [category[0] for category in categories if category[0]]
    
    def add_image_to_project(
        self,
        db: Session,
        project_id: int,
        image_path: str,
        alt_text: Optional[str] = None,
        is_primary: bool = False
    ) -> ProjectImage:
        """Add an image to a project"""
        # Verify project exists
        project = self.get_or_404(db, project_id)
        
        # If this is set as primary, unset other primary images
        if is_primary:
            db.query(ProjectImage).filter(
                ProjectImage.project_id == project_id,
                ProjectImage.is_primary == True
            ).update({"is_primary": False})
        
        # Create new image
        project_image = ProjectImage(
            project_id=project_id,
            image_path=image_path,
            alt_text=alt_text,
            is_primary=is_primary
        )
        
        db.add(project_image)
        db.commit()
        db.refresh(project_image)
        
        return project_image
    
    def remove_image_from_project(
        self,
        db: Session,
        project_id: int,
        image_id: int
    ) -> bool:
        """Remove an image from a project"""
        # Verify project exists
        self.get_or_404(db, project_id)
        
        # Find and delete the image
        image = db.query(ProjectImage).filter(
            and_(
                ProjectImage.id == image_id,
                ProjectImage.project_id == project_id
            )
        ).first()
        
        if not image:
            raise NotFoundError("ProjectImage", image_id)
        
        db.delete(image)
        db.commit()
        
        return True
    
    def update_project_stl_file(
        self,
        db: Session,
        project_id: int,
        stl_file_path: str
    ) -> Project:
        """Update the STL file for a project"""
        project = self.get_or_404(db, project_id)
        project.stl_file = stl_file_path
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return project


# Create service instance
project_service = ProjectService()