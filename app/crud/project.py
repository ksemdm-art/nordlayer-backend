from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.crud.base import CRUDBase
from app.models.project import Project, ProjectImage, ComplexityLevel
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectImageCreate

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects by category."""
        return (
            db.query(Project)
            .filter(Project.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_featured(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get featured projects."""
        return (
            db.query(Project)
            .filter(Project.is_featured == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_title(self, db: Session, *, title: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Search projects by title."""
        return (
            db.query(Project)
            .filter(Project.title.contains(title))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_pricing_info(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects that have pricing information."""
        return (
            db.query(Project)
            .filter(
                and_(
                    Project.estimated_price.isnot(None),
                    Project.estimated_duration_hours.isnot(None)
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_price_range(
        self, 
        db: Session, 
        *, 
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Project]:
        """Get projects within a specific price range."""
        query = db.query(Project)
        
        filters = []
        if min_price is not None:
            filters.append(
                or_(
                    Project.estimated_price >= min_price,
                    Project.price_range_min >= min_price
                )
            )
        if max_price is not None:
            filters.append(
                or_(
                    Project.estimated_price <= max_price,
                    Project.price_range_max <= max_price
                )
            )
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.offset(skip).limit(limit).all()

    def get_by_complexity(
        self, 
        db: Session, 
        *, 
        complexity_levels: List[ComplexityLevel],
        skip: int = 0, 
        limit: int = 100
    ) -> List[Project]:
        """Get projects by complexity level."""
        return (
            db.query(Project)
            .filter(Project.complexity_level.in_(complexity_levels))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_duration_range(
        self, 
        db: Session, 
        *, 
        min_hours: Optional[int] = None,
        max_hours: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Project]:
        """Get projects within a specific duration range."""
        query = db.query(Project)
        
        filters = []
        if min_hours is not None:
            filters.append(Project.estimated_duration_hours >= min_hours)
        if max_hours is not None:
            filters.append(Project.estimated_duration_hours <= max_hours)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.offset(skip).limit(limit).all()

    def get_filtered(
        self,
        db: Session,
        *,
        category: Optional[str] = None,
        complexity_levels: Optional[List[ComplexityLevel]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_hours: Optional[int] = None,
        max_hours: Optional[int] = None,
        is_featured: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get projects with multiple filters applied."""
        query = db.query(Project)
        
        filters = []
        
        if category:
            filters.append(Project.category == category)
        
        if complexity_levels:
            filters.append(Project.complexity_level.in_(complexity_levels))
        
        if min_price is not None:
            filters.append(
                or_(
                    Project.estimated_price >= min_price,
                    Project.price_range_min >= min_price
                )
            )
        
        if max_price is not None:
            filters.append(
                or_(
                    Project.estimated_price <= max_price,
                    Project.price_range_max <= max_price
                )
            )
        
        if min_hours is not None:
            filters.append(Project.estimated_duration_hours >= min_hours)
        
        if max_hours is not None:
            filters.append(Project.estimated_duration_hours <= max_hours)
        
        if is_featured is not None:
            filters.append(Project.is_featured == is_featured)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.offset(skip).limit(limit).all()

class CRUDProjectImage(CRUDBase[ProjectImage, ProjectImageCreate, ProjectImageCreate]):
    def get_by_project(self, db: Session, *, project_id: int) -> List[ProjectImage]:
        """Get all images for a project."""
        return db.query(ProjectImage).filter(ProjectImage.project_id == project_id).all()

    def get_primary_image(self, db: Session, *, project_id: int) -> Optional[ProjectImage]:
        """Get the primary image for a project."""
        return (
            db.query(ProjectImage)
            .filter(ProjectImage.project_id == project_id, ProjectImage.is_primary == True)
            .first()
        )

    def set_primary_image(self, db: Session, *, project_id: int, image_id: int) -> ProjectImage:
        """Set an image as primary for a project."""
        # First, unset all primary images for this project
        db.query(ProjectImage).filter(
            ProjectImage.project_id == project_id,
            ProjectImage.is_primary == True
        ).update({"is_primary": False})
        
        # Set the specified image as primary
        image = db.query(ProjectImage).filter(ProjectImage.id == image_id).first()
        if image:
            image.is_primary = True
            db.commit()
            db.refresh(image)
        return image

project = CRUDProject(Project)
project_image = CRUDProjectImage(ProjectImage)