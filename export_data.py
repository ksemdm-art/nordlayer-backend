"""
Export data from local database to JSON files.
Usage: python export_data.py
"""
import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.article import Article
from app.models.service import Service
from app.models.color import Color
from app.models.project import Project
from app.models.review import Review
from datetime import datetime

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_table(db: Session, model, filename: str):
    """Export table data to JSON file"""
    items = db.query(model).all()
    data = []
    
    for item in items:
        item_dict = {}
        for column in item.__table__.columns:
            value = getattr(item, column.name)
            # Skip id, created_at, updated_at for import
            if column.name not in ['id', 'created_at', 'updated_at']:
                item_dict[column.name] = value
        data.append(item_dict)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=serialize_datetime)
    
    print(f"✅ Exported {len(data)} records to {filename}")

def main():
    db = SessionLocal()
    
    try:
        print("🚀 Starting data export...")
        
        # Export each table
        export_table(db, Article, 'data_export_articles.json')
        export_table(db, Service, 'data_export_services.json')
        export_table(db, Color, 'data_export_colors.json')
        export_table(db, Project, 'data_export_projects.json')
        export_table(db, Review, 'data_export_reviews.json')
        
        print("\n✅ Export complete! Files created:")
        print("  - data_export_articles.json")
        print("  - data_export_services.json")
        print("  - data_export_colors.json")
        print("  - data_export_projects.json")
        print("  - data_export_reviews.json")
        print("\n📤 Upload these files to the server and run import_data.py")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
