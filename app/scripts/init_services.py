"""
Скрипт для инициализации услуг
"""
from app.core.database import SessionLocal
from app.crud.service import service as crud_service
from app.schemas.service import ServiceCreate

def init_services():
    """Создать начальные услуги"""
    db = SessionLocal()
    
    try:
        services_data = [
            {
                "name": "FDM Печать",
                "description": "Технология послойного наплавления пластика. Идеально подходит для прототипирования, функциональных деталей и крупных моделей. Широкий выбор материалов и цветов.",
                "base_price": 50.00,
                "price_factors": {
                    "volume": "от 2₽/см³",
                    "material": "PLA, ABS, PETG",
                    "layer_height": "0.1-0.3мм",
                    "infill": "10-100%",
                    "features": [
                        "Быстрое изготовление",
                        "Экономичная стоимость", 
                        "Большой выбор материалов",
                        "Размеры до 30x30x40 см"
                    ]
                },
                "is_active": True,
                "category": "3d_printing"
            },
            {
                "name": "SLA Печать",
                "description": "Стереолитография обеспечивает высочайшую детализацию и гладкую поверхность. Идеально для ювелирных изделий, миниатюр, стоматологических моделей.",
                "base_price": 100.00,
                "price_factors": {
                    "volume": "от 5₽/см³",
                    "material": "Фотополимеры",
                    "layer_height": "0.025-0.1мм",
                    "support": "Автоматическая генерация",
                    "features": [
                        "Высочайшая детализация",
                        "Гладкая поверхность",
                        "Точность до 0.025мм",
                        "Идеально для миниатюр"
                    ]
                },
                "is_active": True,
                "category": "3d_printing"
            },
            {
                "name": "Постобработка",
                "description": "Профессиональная финишная обработка ваших моделей: шлифовка, покраска, сборка. Превратим ваш прототип в готовое изделие.",
                "base_price": 200.00,
                "price_factors": {
                    "complexity": "Простая/Сложная",
                    "operations": "Шлифовка, покраска, сборка",
                    "time": "1-5 дней",
                    "features": [
                        "Профессиональная покраска",
                        "Шлифовка и полировка",
                        "Сборка сложных моделей",
                        "Нанесение защитных покрытий"
                    ]
                },
                "is_active": True,
                "category": "post_processing"
            },
            {
                "name": "3D Моделирование",
                "description": "Создание 3D моделей по вашим эскизам, чертежам или идеям. Профессиональное моделирование для любых задач.",
                "base_price": 500.00,
                "price_factors": {
                    "complexity": "от 500₽/час",
                    "software": "SolidWorks, Fusion 360, Blender",
                    "formats": "STL, OBJ, STEP, IGES",
                    "features": [
                        "Моделирование по чертежам",
                        "Создание по эскизам",
                        "Оптимизация для печати",
                        "Техническая документация"
                    ]
                },
                "is_active": True,
                "category": "modeling"
            },
            {
                "name": "Консультация",
                "description": "Профессиональная консультация по выбору технологии печати, материалов и оптимизации моделей.",
                "base_price": 0.00,
                "price_factors": {
                    "duration": "30-60 минут",
                    "format": "Онлайн/Офлайн",
                    "topics": "Технологии, материалы, оптимизация",
                    "features": [
                        "Выбор технологии печати",
                        "Подбор материалов",
                        "Оптимизация моделей",
                        "Расчет стоимости"
                    ]
                },
                "is_active": True,
                "category": "consultation"
            }
        ]
        
        created_count = 0
        for service_data in services_data:
            # Проверяем, не существует ли уже услуга с таким названием
            existing = crud_service.get_by_name(db, name=service_data["name"])
            if not existing:
                service_create = ServiceCreate(**service_data)
                crud_service.create(db, obj_in=service_create)
                created_count += 1
                print(f"Создана услуга: {service_data['name']}")
            else:
                print(f"Услуга уже существует: {service_data['name']}")
        
        print(f"\nИнициализация завершена. Создано {created_count} услуг.")
        
    except Exception as e:
        print(f"Ошибка при инициализации услуг: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_services()