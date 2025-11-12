#!/usr/bin/env python3
"""
Script to seed colors data
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.color import Color


def seed_colors():
    """Seed colors data"""
    db: Session = SessionLocal()
    
    try:
        # Check if colors already exist
        existing_colors = db.query(Color).count()
        if existing_colors > 0:
            print(f"Colors already exist ({existing_colors} colors found). Skipping seed.")
            return
        
        # Sample colors for 3D printing
        colors_data = [
            {"name": "Белый", "hex_code": "#FFFFFF", "sort_order": 1},
            {"name": "Черный", "hex_code": "#000000", "sort_order": 2},
            {"name": "Красный", "hex_code": "#EF4444", "sort_order": 3},
            {"name": "Синий", "hex_code": "#3B82F6", "sort_order": 4},
            {"name": "Зеленый", "hex_code": "#10B981", "sort_order": 5},
            {"name": "Желтый", "hex_code": "#F59E0B", "sort_order": 6},
            {"name": "Оранжевый", "hex_code": "#F97316", "sort_order": 7},
            {"name": "Фиолетовый", "hex_code": "#8B5CF6", "sort_order": 8},
            {"name": "Розовый", "hex_code": "#EC4899", "sort_order": 9},
            {"name": "Серый", "hex_code": "#6B7280", "sort_order": 10},
            {"name": "Коричневый", "hex_code": "#92400E", "sort_order": 11},
            {"name": "Прозрачный", "hex_code": "#E5E7EB", "sort_order": 12},
            {"name": "Золотой", "hex_code": "#D97706", "sort_order": 13},
            {"name": "Серебряный", "hex_code": "#9CA3AF", "sort_order": 14},
            {"name": "Медный", "hex_code": "#B45309", "sort_order": 15},
            {"name": "Неоново-зеленый", "hex_code": "#00FF00", "sort_order": 16},
            {"name": "Неоново-розовый", "hex_code": "#FF1493", "sort_order": 17},
            {"name": "Древесный", "hex_code": "#8B4513", "sort_order": 18},
            {"name": "Мраморный", "hex_code": "#F5F5DC", "sort_order": 19},
            {"name": "Металлик", "hex_code": "#C0C0C0", "sort_order": 20}
        ]
        
        # Create color objects
        colors = []
        for color_data in colors_data:
            color = Color(**color_data)
            colors.append(color)
        
        # Add to database
        db.add_all(colors)
        db.commit()
        
        print(f"Successfully seeded {len(colors)} colors")
        
        # Print created colors
        for color in colors:
            print(f"  - {color.name} ({color.hex_code})")
            
    except Exception as e:
        print(f"Error seeding colors: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding colors...")
    seed_colors()
    print("Done!")