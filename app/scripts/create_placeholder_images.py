#!/usr/bin/env python3
"""
Скрипт для создания placeholder изображений для проектов
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.project import Project, ProjectImage

def create_placeholder_image(width: int, height: int, text: str, filename: str):
    """Создает placeholder изображение с текстом"""
    
    # Случайные цвета для разнообразия
    colors = [
        '#3B82F6',  # Blue
        '#10B981',  # Green
        '#F59E0B',  # Yellow
        '#EF4444',  # Red
        '#8B5CF6',  # Purple
        '#06B6D4',  # Cyan
        '#F97316',  # Orange
        '#84CC16',  # Lime
    ]
    
    bg_color = random.choice(colors)
    
    # Создаем изображение
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Пытаемся загрузить шрифт
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # Получаем размеры текста
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Центрируем текст
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Рисуем текст
    draw.text((x, y), text, fill='white', font=font)
    
    # Сохраняем изображение
    image.save(filename, 'JPEG', quality=85)
    print(f"✓ Создано изображение: {filename}")

def create_placeholder_images():
    """Создает placeholder изображения для всех проектов"""
    
    db: Session = SessionLocal()
    
    try:
        # Получаем все проекты с изображениями
        projects = db.query(Project).all()
        
        if not projects:
            print("❌ Проекты не найдены в базе данных")
            return
        
        # Создаем директорию для изображений
        images_dir = Path("static/images")
        images_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎨 Создаем placeholder изображения для {len(projects)} проектов...")
        
        for project in projects:
            print(f"\n📁 Проект: {project.title}")
            
            # Получаем изображения проекта
            project_images = db.query(ProjectImage).filter(
                ProjectImage.project_id == project.id
            ).all()
            
            for i, img in enumerate(project_images):
                # Извлекаем имя файла из пути
                image_path = Path(img.image_path)
                filename = image_path.name
                
                # Создаем полный путь к файлу
                full_path = images_dir / filename
                
                # Создаем placeholder изображение
                if i == 0:
                    # Основное изображение - больше
                    create_placeholder_image(
                        800, 600, 
                        f"{project.title}\n#{project.category}", 
                        str(full_path)
                    )
                else:
                    # Дополнительные изображения
                    create_placeholder_image(
                        600, 400, 
                        f"{project.title}\nВид {i+1}", 
                        str(full_path)
                    )
        
        print(f"\n🎉 Готово! Создано placeholder изображений для всех проектов")
        
    except Exception as e:
        print(f"❌ Ошибка при создании изображений: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Запуск создания placeholder изображений...")
    
    # Проверяем, установлена ли Pillow
    try:
        import PIL
        print("✓ Pillow найден")
    except ImportError:
        print("❌ Pillow не установлен. Установите его командой: pip install Pillow")
        sys.exit(1)
    
    create_placeholder_images()
    print("✅ Готово!")