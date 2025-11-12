#!/usr/bin/env python3
"""
Скрипт для добавления тестовых отзывов
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.review import Review
from app.models.order import Order

def create_test_reviews():
    """Создать тестовые отзывы"""
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже отзывы
        existing_reviews = db.query(Review).count()
        if existing_reviews > 0:
            print(f"Найдено {existing_reviews} отзывов. Пропускаем создание тестовых данных.")
            return
        
        # Получаем существующие заказы
        orders = db.query(Order).all()
        if not orders:
            print("Нет заказов для создания отзывов. Сначала создайте заказы.")
            return
        
        # Тестовые отзывы
        test_reviews = [
            {
                "customer_name": "Анна Петрова",
                "customer_email": "anna.petrova@example.com",
                "rating": 5,
                "title": "Отличное качество печати!",
                "content": "Заказывала прототип детали для своего проекта. Качество печати превзошло все ожидания! Деталь получилась очень точной, все размеры соблюдены. Материал прочный, поверхность гладкая. Обязательно буду заказывать еще!",
                "is_approved": True,
                "is_featured": True
            },
            {
                "customer_name": "Михаил Сидоров",
                "customer_email": "mikhail.sidorov@example.com",
                "rating": 5,
                "title": "Быстро и качественно",
                "content": "Нужно было срочно напечатать корпус для электронного устройства. Заказ выполнили за 2 дня, качество на высоте. Все размеры точные, материал прочный. Рекомендую!",
                "is_approved": True,
                "is_featured": True
            },
            {
                "customer_name": "Елена Козлова",
                "customer_email": "elena.kozlova@example.com",
                "rating": 4,
                "title": "Хорошая работа",
                "content": "Печатали миниатюры для настольной игры. Детализация хорошая, но есть небольшие неровности на некоторых фигурках. В целом результатом довольна, цена адекватная.",
                "is_approved": True,
                "is_featured": False
            },
            {
                "customer_name": "Дмитрий Волков",
                "customer_email": "dmitry.volkov@example.com",
                "rating": 5,
                "title": "Профессиональный подход",
                "content": "Заказывал сложную деталь с множеством мелких элементов. Менеджер помог оптимизировать модель для печати, предложил лучший материал. Результат превосходный! Буду рекомендовать друзьям.",
                "is_approved": True,
                "is_featured": True
            },
            {
                "customer_name": "Ольга Морозова",
                "customer_email": "olga.morozova@example.com",
                "rating": 4,
                "title": "Качественная печать",
                "content": "Печатала декоративные элементы для интерьера. Качество хорошее, цвет соответствует заказанному. Доставка была немного задержана, но в целом все отлично.",
                "is_approved": True,
                "is_featured": False
            },
            {
                "customer_name": "Александр Новиков",
                "customer_email": "alexander.novikov@example.com",
                "rating": 5,
                "title": "Превосходный сервис!",
                "content": "Это уже третий заказ в этой компании. Каждый раз получаю отличный результат. Качество печати стабильно высокое, сроки соблюдаются, цены разумные. Лучший сервис 3D печати в городе!",
                "is_approved": True,
                "is_featured": True
            },
            {
                "customer_name": "Мария Лебедева",
                "customer_email": "maria.lebedeva@example.com",
                "rating": 4,
                "title": "Хороший результат",
                "content": "Заказывала запчасть для старой техники. Деталь подошла идеально, работает как оригинальная. Единственный минус - немного долго ждала, но качество того стоит.",
                "is_approved": True,
                "is_featured": False
            },
            {
                "customer_name": "Сергей Кузнецов",
                "customer_email": "sergey.kuznetsov@example.com",
                "rating": 5,
                "title": "Отличная работа с металлом",
                "content": "Печатали прототип из металлического порошка. Результат поразил - деталь получилась очень прочной и точной. Технология SLM работает отлично. Обязательно закажу серийное производство здесь.",
                "is_approved": True,
                "is_featured": True
            },
            {
                "customer_name": "Татьяна Смирнова",
                "customer_email": "tatyana.smirnova@example.com",
                "rating": 3,
                "title": "Средне",
                "content": "Качество печати нормальное, но есть небольшие дефекты. Цена приемлемая. В следующий раз попробую другой материал, может быть результат будет лучше.",
                "is_approved": True,
                "is_featured": False
            },
            {
                "customer_name": "Игорь Федоров",
                "customer_email": "igor.fedorov@example.com",
                "rating": 5,
                "title": "Рекомендую всем!",
                "content": "Заказывал архитектурный макет. Детализация потрясающая, все элементы проработаны до мелочей. Клиент был в восторге от презентации. Спасибо за профессиональную работу!",
                "is_approved": True,
                "is_featured": True
            }
        ]
        
        # Создаем отзывы
        created_count = 0
        for i, review_data in enumerate(test_reviews):
            if i >= len(orders):
                break
                
            # Используем существующий заказ
            order = orders[i]
            
            # Создаем отзыв с датой в прошлом
            days_ago = random.randint(1, 90)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            review = Review(
                order_id=order.id,
                customer_name=review_data["customer_name"],
                customer_email=review_data["customer_email"],
                rating=review_data["rating"],
                title=review_data["title"],
                content=review_data["content"],
                is_approved=review_data["is_approved"],
                is_featured=review_data["is_featured"],
                created_at=created_at,
                updated_at=created_at
            )
            
            db.add(review)
            created_count += 1
        
        db.commit()
        print(f"Создано {created_count} тестовых отзывов")
        
        # Выводим статистику
        total_reviews = db.query(Review).filter(Review.is_approved == True).count()
        avg_rating = db.query(Review.rating).filter(Review.is_approved == True).all()
        if avg_rating:
            avg_rating = sum(r[0] for r in avg_rating) / len(avg_rating)
            print(f"Общее количество одобренных отзывов: {total_reviews}")
            print(f"Средняя оценка: {avg_rating:.1f}")
        
    except Exception as e:
        print(f"Ошибка при создании тестовых отзывов: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_reviews()