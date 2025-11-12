"""
Скрипт для инициализации начального контента CMS
"""
from app.core.database import SessionLocal
from app.crud.content import content as crud_content
from app.schemas.content import ContentCreate

def init_content():
    """Создать начальный контент для сайта"""
    db = SessionLocal()
    
    try:
        # Контент для главной страницы
        home_content = [
            {
                "key": "home.hero.title",
                "content": "Профессиональная 3D печать на заказ",
                "content_type": "text",
                "description": "Заголовок главной страницы",
                "group_name": "home",
                "sort_order": "1"
            },
            {
                "key": "home.hero.subtitle",
                "content": "Превращаем ваши идеи в реальность с помощью современных технологий 3D печати",
                "content_type": "text",
                "description": "Подзаголовок главной страницы",
                "group_name": "home",
                "sort_order": "2"
            },
            {
                "key": "home.hero.cta_text",
                "content": "Заказать печать",
                "content_type": "text",
                "description": "Текст кнопки призыва к действию",
                "group_name": "home",
                "sort_order": "3"
            },
            {
                "key": "home.features.title",
                "content": "Почему выбирают нас",
                "content_type": "text",
                "description": "Заголовок секции преимуществ",
                "group_name": "home",
                "sort_order": "4"
            },
            {
                "key": "home.features.items",
                "json_content": [
                    {
                        "title": "Высокое качество",
                        "description": "Используем профессиональное оборудование и качественные материалы",
                        "icon": "quality"
                    },
                    {
                        "title": "Быстрые сроки",
                        "description": "Выполняем заказы в кратчайшие сроки без потери качества",
                        "icon": "speed"
                    },
                    {
                        "title": "Доступные цены",
                        "description": "Конкурентные цены на все виды 3D печати",
                        "icon": "price"
                    },
                    {
                        "title": "Индивидуальный подход",
                        "description": "Консультируем по каждому проекту и помогаем выбрать оптимальное решение",
                        "icon": "support"
                    }
                ],
                "content_type": "json",
                "description": "Список преимуществ на главной странице",
                "group_name": "home",
                "sort_order": "5"
            }
        ]
        
        # Контент для страницы услуг
        services_content = [
            {
                "key": "services.title",
                "content": "Наши услуги",
                "content_type": "text",
                "description": "Заголовок страницы услуг",
                "group_name": "services",
                "sort_order": "1"
            },
            {
                "key": "services.subtitle",
                "content": "Полный спектр услуг 3D печати для любых задач",
                "content_type": "text",
                "description": "Подзаголовок страницы услуг",
                "group_name": "services",
                "sort_order": "2"
            },
            {
                "key": "services.cta.title",
                "content": "Готовы начать проект?",
                "content_type": "text",
                "description": "Заголовок призыва к действию",
                "group_name": "services",
                "sort_order": "3"
            },
            {
                "key": "services.cta.description",
                "content": "Свяжитесь с нами для консультации и расчета стоимости вашего проекта",
                "content_type": "text",
                "description": "Описание призыва к действию",
                "group_name": "services",
                "sort_order": "4"
            }
        ]
        
        # Контент для галереи
        gallery_content = [
            {
                "key": "gallery.title",
                "content": "Галерея проектов",
                "content_type": "text",
                "description": "Заголовок галереи",
                "group_name": "gallery",
                "sort_order": "1"
            },
            {
                "key": "gallery.subtitle",
                "content": "Примеры наших работ и реализованных проектов",
                "content_type": "text",
                "description": "Подзаголовок галереи",
                "group_name": "gallery",
                "sort_order": "2"
            }
        ]
        
        # Контент для блога
        blog_content = [
            {
                "key": "blog.title",
                "content": "Блог о 3D печати",
                "content_type": "text",
                "description": "Заголовок блога",
                "group_name": "blog",
                "sort_order": "1"
            },
            {
                "key": "blog.subtitle",
                "content": "Новости, советы и обучающие материалы о 3D печати",
                "content_type": "text",
                "description": "Подзаголовок блога",
                "group_name": "blog",
                "sort_order": "2"
            }
        ]
        
        # Общий контент
        common_content = [
            {
                "key": "site.name",
                "content": "3D Print Pro",
                "content_type": "text",
                "description": "Название сайта",
                "group_name": "common",
                "sort_order": "1"
            },
            {
                "key": "site.tagline",
                "content": "Профессиональные услуги 3D печати",
                "content_type": "text",
                "description": "Слоган сайта",
                "group_name": "common",
                "sort_order": "2"
            },
            {
                "key": "contact.phone",
                "content": "+7 (999) 123-45-67",
                "content_type": "text",
                "description": "Телефон для связи",
                "group_name": "contact",
                "sort_order": "1"
            },
            {
                "key": "contact.email",
                "content": "info@3dprintpro.ru",
                "content_type": "text",
                "description": "Email для связи",
                "group_name": "contact",
                "sort_order": "2"
            },
            {
                "key": "contact.address",
                "content": "г. Москва, ул. Примерная, д. 123",
                "content_type": "text",
                "description": "Адрес",
                "group_name": "contact",
                "sort_order": "3"
            }
        ]
        
        # Объединяем весь контент
        all_content = home_content + services_content + gallery_content + blog_content + common_content
        
        # Создаем контент
        created_count = 0
        for content_data in all_content:
            # Проверяем, не существует ли уже контент с таким ключом
            existing = crud_content.get_by_key(db, key=content_data["key"])
            if not existing:
                content_create = ContentCreate(**content_data)
                crud_content.create(db, obj_in=content_create)
                created_count += 1
                print(f"Создан контент: {content_data['key']}")
            else:
                print(f"Контент уже существует: {content_data['key']}")
        
        print(f"\nИнициализация завершена. Создано {created_count} элементов контента.")
        
    except Exception as e:
        print(f"Ошибка при инициализации контента: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_content()