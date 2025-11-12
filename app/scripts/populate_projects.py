#!/usr/bin/env python3
"""
Скрипт для заполнения базы данных фейковыми проектами для галереи
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from models.project import Project, ProjectImage
from models.base import Base

# Создаем таблицы если их нет
Base.metadata.create_all(bind=engine)

# Фейковые данные проектов
FAKE_PROJECTS = [
    {
        "title": "Миниатюра дракона",
        "description": "Детализированная миниатюра дракона для настольных игр. Модель включает в себя множество мелких деталей и текстур, что делает её идеальной для коллекционеров и любителей настольных игр. Печать выполнена с высоким разрешением для максимальной детализации.",
        "category": "miniatures",
        "stl_file": "/static/models/dragon.stl",
        "is_featured": True,
        "project_metadata": {
            "print_time": "4 часа",
            "material": "PLA",
            "layer_height": "0.1mm",
            "infill": "15%",
            "supports": True,
            "difficulty": "Средний"
        },
        "images": [
            {"image_path": "/static/images/dragon-1.jpg", "alt_text": "Миниатюра дракона - вид спереди", "is_primary": True},
            {"image_path": "/static/images/dragon-2.jpg", "alt_text": "Миниатюра дракона - вид сбоку", "is_primary": False},
            {"image_path": "/static/images/dragon-3.jpg", "alt_text": "Миниатюра дракона - детали", "is_primary": False}
        ]
    },
    {
        "title": "Прототип корпуса устройства",
        "description": "Функциональный прототип корпуса для электронного устройства с точными размерами и креплениями. Идеально подходит для тестирования компонентов перед массовым производством.",
        "category": "prototypes",
        "stl_file": "/static/models/device-case.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "6 часов",
            "material": "PETG",
            "layer_height": "0.2mm",
            "infill": "25%",
            "supports": False,
            "difficulty": "Легкий"
        },
        "images": [
            {"image_path": "/static/images/device-case-1.jpg", "alt_text": "Корпус устройства", "is_primary": True},
            {"image_path": "/static/images/device-case-2.jpg", "alt_text": "Корпус устройства - внутренняя часть", "is_primary": False}
        ]
    },
    {
        "title": "Декоративная ваза 'Геометрия'",
        "description": "Элегантная ваза с геометрическим узором, идеально подходящая для современного интерьера. Уникальный дизайн создает красивую игру света и тени.",
        "category": "decorative",
        "stl_file": "/static/models/geometric-vase.stl",
        "is_featured": True,
        "project_metadata": {
            "print_time": "8 часов",
            "material": "PLA Silk",
            "layer_height": "0.15mm",
            "infill": "10%",
            "supports": False,
            "difficulty": "Средний"
        },
        "images": [
            {"image_path": "/static/images/vase-1.jpg", "alt_text": "Декоративная ваза", "is_primary": True},
            {"image_path": "/static/images/vase-2.jpg", "alt_text": "Ваза с цветами", "is_primary": False},
            {"image_path": "/static/images/vase-3.jpg", "alt_text": "Детали узора", "is_primary": False}
        ]
    },
    {
        "title": "Функциональный держатель для телефона",
        "description": "Практичный держатель для смартфона с регулируемым углом наклона. Подходит для большинства современных телефонов и планшетов.",
        "category": "functional",
        "stl_file": "/static/models/phone-holder.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "2 часа",
            "material": "PLA",
            "layer_height": "0.2mm",
            "infill": "20%",
            "supports": False,
            "difficulty": "Легкий"
        },
        "images": [
            {"image_path": "/static/images/phone-holder-1.jpg", "alt_text": "Держатель для телефона", "is_primary": True},
            {"image_path": "/static/images/phone-holder-2.jpg", "alt_text": "Держатель с телефоном", "is_primary": False}
        ]
    },
    {
        "title": "Архитектурная модель офисного здания",
        "description": "Масштабная модель современного офисного здания с детализированным фасадом. Отличный пример архитектурного моделирования для презентаций.",
        "category": "architectural",
        "stl_file": "/static/models/office-building.stl",
        "is_featured": True,
        "project_metadata": {
            "print_time": "12 часов",
            "material": "PLA",
            "layer_height": "0.1mm",
            "infill": "15%",
            "supports": True,
            "difficulty": "Сложный"
        },
        "images": [
            {"image_path": "/static/images/building-1.jpg", "alt_text": "Модель здания", "is_primary": True},
            {"image_path": "/static/images/building-2.jpg", "alt_text": "Детали фасада", "is_primary": False},
            {"image_path": "/static/images/building-3.jpg", "alt_text": "Вид сверху", "is_primary": False}
        ]
    },
    {
        "title": "Ювелирное кольцо 'Infinity'",
        "description": "Изящное кольцо с уникальным дизайном в виде символа бесконечности. Напечатано из специального материала, подходящего для ювелирных изделий.",
        "category": "jewelry",
        "stl_file": "/static/models/infinity-ring.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "3 часа",
            "material": "Resin",
            "layer_height": "0.05mm",
            "infill": "100%",
            "supports": True,
            "difficulty": "Сложный"
        },
        "images": [
            {"image_path": "/static/images/ring-1.jpg", "alt_text": "Кольцо Infinity", "is_primary": True},
            {"image_path": "/static/images/ring-2.jpg", "alt_text": "Кольцо на руке", "is_primary": False}
        ]
    },
    {
        "title": "Автомобильный держатель для напитков",
        "description": "Кастомный держатель для напитков, разработанный специально для определенной модели автомобиля. Идеально вписывается в интерьер салона.",
        "category": "automotive",
        "stl_file": "/static/models/cup-holder.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "4 часа",
            "material": "PETG",
            "layer_height": "0.2mm",
            "infill": "30%",
            "supports": False,
            "difficulty": "Средний"
        },
        "images": [
            {"image_path": "/static/images/cup-holder-1.jpg", "alt_text": "Держатель для напитков", "is_primary": True},
            {"image_path": "/static/images/cup-holder-2.jpg", "alt_text": "Установленный держатель", "is_primary": False}
        ]
    },
    {
        "title": "Медицинский тренажер для хирургии",
        "description": "Анатомически точная модель для обучения хирургическим процедурам. Используется в медицинских учебных заведениях для практических занятий.",
        "category": "medical",
        "stl_file": "/static/models/surgical-trainer.stl",
        "is_featured": True,
        "project_metadata": {
            "print_time": "10 часов",
            "material": "TPU",
            "layer_height": "0.15mm",
            "infill": "20%",
            "supports": True,
            "difficulty": "Сложный"
        },
        "images": [
            {"image_path": "/static/images/medical-1.jpg", "alt_text": "Медицинский тренажер", "is_primary": True},
            {"image_path": "/static/images/medical-2.jpg", "alt_text": "Детали анатомии", "is_primary": False}
        ]
    },
    {
        "title": "Игровая миниатюра воина",
        "description": "Детализированная фигурка воина для настольных ролевых игр. Высокая детализация доспехов и оружия делает её идеальной для коллекционирования.",
        "category": "miniatures",
        "stl_file": "/static/models/warrior-mini.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "5 часов",
            "material": "Resin",
            "layer_height": "0.05mm",
            "infill": "100%",
            "supports": True,
            "difficulty": "Сложный"
        },
        "images": [
            {"image_path": "/static/images/warrior-1.jpg", "alt_text": "Миниатюра воина", "is_primary": True},
            {"image_path": "/static/images/warrior-2.jpg", "alt_text": "Детали доспехов", "is_primary": False},
            {"image_path": "/static/images/warrior-3.jpg", "alt_text": "Раскрашенная миниатюра", "is_primary": False}
        ]
    },
    {
        "title": "Органайзер для инструментов",
        "description": "Функциональный органайзер для мастерской с отделениями для различных инструментов. Помогает поддерживать порядок на рабочем месте.",
        "category": "functional",
        "stl_file": "/static/models/tool-organizer.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "7 часов",
            "material": "PETG",
            "layer_height": "0.2mm",
            "infill": "25%",
            "supports": False,
            "difficulty": "Легкий"
        },
        "images": [
            {"image_path": "/static/images/organizer-1.jpg", "alt_text": "Органайзер для инструментов", "is_primary": True},
            {"image_path": "/static/images/organizer-2.jpg", "alt_text": "Заполненный органайзер", "is_primary": False}
        ]
    },
    {
        "title": "Декоративная лампа 'Волны'",
        "description": "Современная настольная лампа с уникальным дизайном в виде волн. Создает мягкое рассеянное освещение и служит украшением интерьера.",
        "category": "decorative",
        "stl_file": "/static/models/wave-lamp.stl",
        "is_featured": True,
        "project_metadata": {
            "print_time": "9 часов",
            "material": "PLA Translucent",
            "layer_height": "0.15mm",
            "infill": "5%",
            "supports": True,
            "difficulty": "Средний"
        },
        "images": [
            {"image_path": "/static/images/lamp-1.jpg", "alt_text": "Лампа Волны", "is_primary": True},
            {"image_path": "/static/images/lamp-2.jpg", "alt_text": "Включенная лампа", "is_primary": False},
            {"image_path": "/static/images/lamp-3.jpg", "alt_text": "Детали дизайна", "is_primary": False}
        ]
    },
    {
        "title": "Прототип корпуса дрона",
        "description": "Легкий и прочный корпус для квадрокоптера, разработанный с учетом аэродинамических характеристик. Включает крепления для всех компонентов.",
        "category": "prototypes",
        "stl_file": "/static/models/drone-frame.stl",
        "is_featured": False,
        "project_metadata": {
            "print_time": "8 часов",
            "material": "Carbon Fiber PLA",
            "layer_height": "0.2mm",
            "infill": "20%",
            "supports": True,
            "difficulty": "Сложный"
        },
        "images": [
            {"image_path": "/static/images/drone-1.jpg", "alt_text": "Корпус дрона", "is_primary": True},
            {"image_path": "/static/images/drone-2.jpg", "alt_text": "Собранный дрон", "is_primary": False}
        ]
    }
]

def populate_projects():
    """Заполняет базу данных фейковыми проектами"""
    db: Session = SessionLocal()
    
    try:
        # Проверяем, есть ли уже проекты в базе
        existing_count = db.query(Project).count()
        if existing_count > 0:
            print(f"В базе уже есть {existing_count} проектов. Очищаем...")
            # Удаляем существующие проекты
            db.query(ProjectImage).delete()
            db.query(Project).delete()
            db.commit()
        
        print("Добавляем фейковые проекты...")
        
        for project_data in FAKE_PROJECTS:
            # Извлекаем данные изображений
            images_data = project_data.pop("images", [])
            
            # Создаем проект
            project = Project(**project_data)
            db.add(project)
            db.flush()  # Получаем ID проекта
            
            # Добавляем изображения
            for image_data in images_data:
                image = ProjectImage(
                    project_id=project.id,
                    **image_data
                )
                db.add(image)
            
            print(f"✓ Добавлен проект: {project.title}")
        
        db.commit()
        
        # Выводим статистику
        total_projects = db.query(Project).count()
        featured_projects = db.query(Project).filter(Project.is_featured == True).count()
        total_images = db.query(ProjectImage).count()
        
        print(f"\n🎉 Успешно добавлено:")
        print(f"   📁 Проектов: {total_projects}")
        print(f"   ⭐ Рекомендуемых: {featured_projects}")
        print(f"   🖼️  Изображений: {total_images}")
        
        # Статистика по категориям
        print(f"\n📊 По категориям:")
        from sqlalchemy import func
        categories = db.query(Project.category, func.count(Project.id)).group_by(Project.category).all()
        category_names = {
            'miniatures': 'Миниатюры',
            'prototypes': 'Прототипы',
            'decorative': 'Декоративные',
            'functional': 'Функциональные',
            'architectural': 'Архитектурные',
            'jewelry': 'Ювелирные',
            'automotive': 'Автомобильные',
            'medical': 'Медицинские'
        }
        
        for category, count in categories:
            name = category_names.get(category, category)
            print(f"   {name}: {count}")
            
    except Exception as e:
        print(f"❌ Ошибка при добавлении проектов: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Запуск скрипта заполнения проектов...")
    populate_projects()
    print("✅ Готово!")