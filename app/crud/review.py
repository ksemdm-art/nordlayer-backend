from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.crud.base import CRUDBase
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewModerationUpdate

class CRUDReview(CRUDBase[Review, ReviewCreate, ReviewUpdate]):
    def create(self, db: Session, *, obj_in: ReviewCreate) -> Review:
        """Create a new review."""
        obj_in_data = obj_in.model_dump()
        
        # Convert images list to JSON format if provided
        if obj_in_data.get('images'):
            obj_in_data['images'] = [img.model_dump() if hasattr(img, 'model_dump') else img for img in obj_in_data['images']]
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_email(self, db: Session, *, customer_email: str) -> List[Review]:
        """Get reviews by customer email."""
        return db.query(Review).filter(Review.customer_email == customer_email).all()

    def get_approved(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Review]:
        """Get all approved reviews."""
        return (
            db.query(Review)
            .filter(Review.is_approved == True)
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_featured(self, db: Session, *, skip: int = 0, limit: int = 10) -> List[Review]:
        """Get featured reviews."""
        return (
            db.query(Review)
            .filter(and_(Review.is_approved == True, Review.is_featured == True))
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pending_moderation(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Review]:
        """Get reviews pending moderation."""
        return (
            db.query(Review)
            .filter(Review.is_approved == False)
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_rating(self, db: Session, *, rating: int, skip: int = 0, limit: int = 100) -> List[Review]:
        """Get approved reviews by rating."""
        return (
            db.query(Review)
            .filter(and_(Review.is_approved == True, Review.rating == rating))
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_rating_range(self, db: Session, *, min_rating: int, max_rating: int, skip: int = 0, limit: int = 100) -> List[Review]:
        """Get approved reviews by rating range."""
        return (
            db.query(Review)
            .filter(and_(
                Review.is_approved == True,
                Review.rating >= min_rating,
                Review.rating <= max_rating
            ))
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def approve_review(self, db: Session, *, review_id: int) -> Optional[Review]:
        """Approve a review."""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            review.is_approved = True
            db.commit()
            db.refresh(review)
        return review

    def reject_review(self, db: Session, *, review_id: int) -> Optional[Review]:
        """Reject a review."""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            review.is_approved = False
            db.commit()
            db.refresh(review)
        return review

    def set_featured(self, db: Session, *, review_id: int, featured: bool = True) -> Optional[Review]:
        """Set review as featured or unfeatured."""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review and review.is_approved:
            review.is_featured = featured
            db.commit()
            db.refresh(review)
        return review

    def moderate_review(self, db: Session, *, review_id: int, moderation_data: ReviewModerationUpdate) -> Optional[Review]:
        """Update review moderation status."""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            update_data = moderation_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(review, field, value)
            db.commit()
            db.refresh(review)
        return review

    def get_average_rating(self, db: Session) -> float:
        """Get average rating of all approved reviews."""
        from sqlalchemy import func
        result = db.query(func.avg(Review.rating)).filter(Review.is_approved == True).scalar()
        return float(result) if result else 0.0

    def get_rating_distribution(self, db: Session) -> dict:
        """Get distribution of ratings for approved reviews."""
        from sqlalchemy import func
        results = (
            db.query(Review.rating, func.count(Review.rating))
            .filter(Review.is_approved == True)
            .group_by(Review.rating)
            .all()
        )
        return {rating: count for rating, count in results}

    def search_by_content(self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100) -> List[Review]:
        """Search approved reviews by content or title."""
        return (
            db.query(Review)
            .filter(and_(
                Review.is_approved == True,
                (Review.content.contains(search_term) | Review.title.contains(search_term))
            ))
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        approved_only: bool = False,
        featured_only: bool = False
    ) -> List[Review]:
        """Get multiple reviews with optional filtering."""
        query = db.query(self.model)
        
        if approved_only:
            query = query.filter(self.model.is_approved == True)
        
        if featured_only:
            query = query.filter(and_(self.model.is_approved == True, self.model.is_featured == True))
        
        return query.order_by(desc(self.model.created_at)).offset(skip).limit(limit).all()

    def count(self, db: Session, *, approved_only: bool = True) -> int:
        """Count reviews with optional filtering for approved only."""
        query = db.query(self.model)
        
        if approved_only:
            query = query.filter(self.model.is_approved == True)
        
        return query.count()

review = CRUDReview(Review)