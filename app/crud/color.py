from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException

from app.crud.base import CRUDBase
from app.models.color import Color, ColorType
from app.schemas.color import ColorCreate, ColorUpdate


class CRUDColor(CRUDBase[Color, ColorCreate, ColorUpdate]):
    def get_active_colors(self, db: Session) -> List[Color]:
        """Get all active colors ordered by sort_order"""
        return db.query(Color).filter(
            Color.is_active == True
        ).order_by(Color.sort_order, Color.name).all()
    
    def get_colors_by_type(self, db: Session, *, color_type: ColorType) -> List[Color]:
        """Get all active colors of a specific type"""
        return db.query(Color).filter(
            and_(Color.is_active == True, Color.type == color_type)
        ).order_by(Color.sort_order, Color.name).all()
    
    def get_new_colors(self, db: Session, limit: int = 10) -> List[Color]:
        """Get new colors (marked as is_new=True)"""
        return db.query(Color).filter(
            and_(Color.is_active == True, Color.is_new == True)
        ).order_by(Color.created_at.desc()).limit(limit).all()
    
    def get_all_colors_for_admin(self, db: Session, skip: int = 0, limit: int = 100) -> List[Color]:
        """Get all colors for admin panel (including inactive)"""
        return db.query(Color).order_by(
            Color.is_active.desc(), Color.sort_order, Color.name
        ).offset(skip).limit(limit).all()
    
    def toggle_active_status(self, db: Session, *, color_id: int) -> Color:
        """Toggle active status of a color"""
        color = self.get(db, id=color_id)
        if not color:
            raise HTTPException(status_code=404, detail="Color not found")
        
        color.is_active = not color.is_active
        db.add(color)
        db.commit()
        db.refresh(color)
        return color
    
    def toggle_new_status(self, db: Session, *, color_id: int) -> Color:
        """Toggle new status of a color"""
        color = self.get(db, id=color_id)
        if not color:
            raise HTTPException(status_code=404, detail="Color not found")
        
        color.is_new = not color.is_new
        db.add(color)
        db.commit()
        db.refresh(color)
        return color
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Color]:
        """Get color by name"""
        return db.query(Color).filter(Color.name == name).first()
    
    def get_by_hex_code(self, db: Session, *, hex_code: str) -> Optional[Color]:
        """Get color by hex code (for solid colors only)"""
        return db.query(Color).filter(
            and_(Color.hex_code == hex_code, Color.type == ColorType.SOLID)
        ).first()
    
    def create(self, db: Session, *, obj_in: ColorCreate) -> Color:
        """Create color with validation for different types"""
        # Validate color data based on type
        self._validate_color_data(obj_in.dict())
        
        return super().create(db, obj_in=obj_in)
    
    def update(self, db: Session, *, db_obj: Color, obj_in: ColorUpdate) -> Color:
        """Update color with validation for different types"""
        update_data = obj_in.dict(exclude_unset=True)
        
        # If type is being changed, validate the new data
        if "type" in update_data:
            # Merge existing data with update data for validation
            validation_data = {**db_obj.__dict__, **update_data}
            self._validate_color_data(validation_data)
        
        return super().update(db, db_obj=db_obj, obj_in=obj_in)
    
    def _validate_color_data(self, data: Dict[str, Any]) -> None:
        """Validate color data based on type"""
        color_type = data.get("type", ColorType.SOLID)
        
        if color_type == ColorType.SOLID:
            if not data.get("hex_code"):
                raise HTTPException(
                    status_code=400,
                    detail="Solid colors must have a hex_code"
                )
            # Validate hex code format
            hex_code = data["hex_code"]
            if not (hex_code.startswith("#") and len(hex_code) == 7):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid hex code format. Must be #RRGGBB"
                )
        
        elif color_type == ColorType.GRADIENT:
            gradient_colors = data.get("gradient_colors")
            if not gradient_colors or not isinstance(gradient_colors, list) or len(gradient_colors) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Gradient colors must have at least 2 color stops"
                )
            
            # Validate each gradient stop
            for stop in gradient_colors:
                if not isinstance(stop, dict) or "color" not in stop or "position" not in stop:
                    raise HTTPException(
                        status_code=400,
                        detail="Each gradient stop must have 'color' and 'position' fields"
                    )
                
                # Validate hex code in gradient stop
                hex_code = stop["color"]
                if not (hex_code.startswith("#") and len(hex_code) == 7):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid hex code in gradient stop: {hex_code}"
                    )
                
                # Validate position (0-100)
                position = stop["position"]
                if not isinstance(position, (int, float)) or position < 0 or position > 100:
                    raise HTTPException(
                        status_code=400,
                        detail="Gradient position must be between 0 and 100"
                    )
            
            # Validate gradient direction
            gradient_direction = data.get("gradient_direction", "linear")
            if gradient_direction not in ["linear", "radial"]:
                raise HTTPException(
                    status_code=400,
                    detail="Gradient direction must be 'linear' or 'radial'"
                )
        
        elif color_type == ColorType.METALLIC:
            if not data.get("metallic_base"):
                raise HTTPException(
                    status_code=400,
                    detail="Metallic colors must have a metallic_base hex code"
                )
            
            # Validate metallic base hex code
            hex_code = data["metallic_base"]
            if not (hex_code.startswith("#") and len(hex_code) == 7):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metallic_base hex code format. Must be #RRGGBB"
                )
            
            # Validate metallic intensity
            intensity = data.get("metallic_intensity", 0.5)
            if not isinstance(intensity, (int, float)) or intensity < 0 or intensity > 1:
                raise HTTPException(
                    status_code=400,
                    detail="Metallic intensity must be between 0.0 and 1.0"
                )
        
        # Validate price modifier
        price_modifier = data.get("price_modifier", 1.0)
        if not isinstance(price_modifier, (int, float)) or price_modifier <= 0:
            raise HTTPException(
                status_code=400,
                detail="Price modifier must be a positive number"
            )


color = CRUDColor(Color)