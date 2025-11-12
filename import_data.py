"""
Import data from JSON files to database.
Usage: python import_data.py
"""
import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.article import Article
from app.models.service import Service
from app.models.color import Color
from app.models.project import Project
from app.models.review import Review

def import_table(db: Session, model, filename: str):
    """Import table data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for item_data in data:
            # Create new instance
            item = model(**item_data)
            db.add(item)
            count += 1
        
        db.commit()
        print(f"✅ Imported {count} records from {filename}")
        
    except FileNotFoundError:
        print(f"⚠️  File {filename} not found, skipping...")
    except Exception as e:
        print(f"❌ Error importing {filename}: {e}")
        db.rollback()

def main():
    db = SessionLocal()
    
    try:
        print("🚀 Starting data import...")
        print("⚠️  This will add data to existing tables (not replace)")
        
        response = input("\nContinue? (yes/no): ")
        if response.lower() != 'yes':
            print("Import cancelled")
            return
        
        # Import each table
        import_table(db, Article, 'data_export_articles.json')
        import_table(db, Service, 'data_export_services.json')
        import_table(db, Color, 'data_export_colors.json')
        import_table(db, Project, 'data_export_projects.json')
        import_table(db, Review, 'data_export_reviews.json')
        
        print("\n✅ Import complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
