"""
Email templates for different notification types.
"""
from typing import Dict, Any
from datetime import datetime


class EmailTemplates:
    """Collection of email templates for notifications"""
    
    @staticmethod
    def order_confirmation_html(order_data: Dict[str, Any]) -> str:
        """HTML template for order confirmation email"""
        customer_name = order_data.get('customer_name', 'Уважаемый клиент')
        order_id = order_data.get('id', 'N/A')
        service_name = order_data.get('service_name', 'Не указана')
        status = order_data.get('status', 'Новый')
        created_at = order_data.get('created_at', datetime.now().strftime('%d.%m.%Y %H:%M'))
        
        # Extract specifications
        specs = order_data.get('specifications') or {}
        material = specs.get('material', 'Не указан')
        quality = specs.get('quality', 'Не указано')
        infill = specs.get('infill', 'Не указано')
        files_count = len(specs.get('files_info', []))
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Подтверждение заказа - NordLayer</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1B2A41; background-color: #F4F7FA; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        .header {{ background: linear-gradient(135deg, #1B2A41 0%, #8E9BAE 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .order-details {{ background: #F4F7FA; padding: 15px; border-radius: 6px; margin: 15px 0; }}
        .specs {{ background: #F4F7FA; padding: 15px; border-radius: 6px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #8E9BAE; font-size: 14px; }}
        .accent {{ color: #C68642; font-weight: bold; }}
        .status {{ background: #C68642; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NordLayer</h1>
            <p>Мастерская цифрового ремесла из Карелии</p>
        </div>
        
        <div class="content">
            <h2>Здравствуйте, {customer_name}!</h2>
            
            <p>Ваш заказ успешно принят и находится в обработке. Слой за слоем мы создадим для вас нечто особенное.</p>
            
            <div class="order-details">
                <h3>Детали заказа</h3>
                <p><strong>Номер заказа:</strong> <span class="accent">#{order_id}</span></p>
                <p><strong>Услуга:</strong> {service_name}</p>
                <p><strong>Статус:</strong> <span class="status">{status}</span></p>
                <p><strong>Дата создания:</strong> {created_at}</p>
            </div>
            
            <div class="specs">
                <h3>Параметры печати</h3>
                <p><strong>Материал:</strong> {material}</p>
                <p><strong>Качество:</strong> {quality}</p>
                <p><strong>Заполнение:</strong> {infill}%</p>
                <p><strong>Файлов загружено:</strong> {files_count}</p>
            </div>
            
            <p>Мы свяжемся с вами в ближайшее время для уточнения деталей и согласования сроков выполнения.</p>
            
            <p>Если у вас есть вопросы, не стесняйтесь обращаться к нам.</p>
        </div>
        
        <div class="footer">
            <p><strong>NordLayer</strong><br>
            Мастерская цифрового ремесла из Карелии<br>
            <em>Мы не просто печатаем — мы создаём вещи с душой</em></p>
        </div>
    </div>
</body>
</html>
"""
    
    @staticmethod
    def order_confirmation_text(order_data: Dict[str, Any]) -> str:
        """Plain text template for order confirmation email"""
        customer_name = order_data.get('customer_name', 'Уважаемый клиент')
        order_id = order_data.get('id', 'N/A')
        service_name = order_data.get('service_name', 'Не указана')
        status = order_data.get('status', 'Новый')
        created_at = order_data.get('created_at', datetime.now().strftime('%d.%m.%Y %H:%M'))
        
        # Extract specifications
        specs = order_data.get('specifications') or {}
        material = specs.get('material', 'Не указан')
        quality = specs.get('quality', 'Не указано')
        infill = specs.get('infill', 'Не указано')
        files_count = len(specs.get('files_info', []))
        
        return f"""
Здравствуйте, {customer_name}!

Ваш заказ успешно принят и находится в обработке.
Слой за слоем мы создадим для вас нечто особенное.

ДЕТАЛИ ЗАКАЗА:
• Номер заказа: #{order_id}
• Услуга: {service_name}
• Статус: {status}
• Дата создания: {created_at}

ПАРАМЕТРЫ ПЕЧАТИ:
• Материал: {material}
• Качество: {quality}
• Заполнение: {infill}%
• Файлов загружено: {files_count}

Мы свяжемся с вами в ближайшее время для уточнения деталей 
и согласования сроков выполнения.

Если у вас есть вопросы, не стесняйтесь обращаться к нам.

С уважением,
Команда NordLayer
Мастерская цифрового ремесла из Карелии

"Мы не просто печатаем — мы создаём вещи с душой"
"""
    
    @staticmethod
    def status_change_html(order_data: Dict[str, Any]) -> str:
        """HTML template for status change notification"""
        customer_name = order_data.get('customer_name', 'Уважаемый клиент')
        order_id = order_data.get('id', 'N/A')
        service_name = order_data.get('service_name', 'Не указана')
        status = order_data.get('status', 'unknown')
        
        status_messages = {
            "confirmed": "подтвержден и принят в работу",
            "in_progress": "выполняется",
            "ready": "готов к получению",
            "completed": "завершен",
            "cancelled": "отменен"
        }
        
        status_text = status_messages.get(status, f"изменен на: {status}")
        status_color = {
            "confirmed": "#C68642",
            "in_progress": "#1B2A41",
            "ready": "#28a745",
            "completed": "#28a745",
            "cancelled": "#dc3545"
        }.get(status, "#8E9BAE")
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Изменение статуса заказа - NordLayer</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1B2A41; background-color: #F4F7FA; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        .header {{ background: linear-gradient(135deg, #1B2A41 0%, #8E9BAE 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .status-update {{ background: #F4F7FA; padding: 20px; border-radius: 6px; margin: 15px 0; text-align: center; }}
        .status {{ background: {status_color}; color: white; padding: 8px 16px; border-radius: 20px; font-size: 16px; font-weight: bold; }}
        .order-info {{ background: #F4F7FA; padding: 15px; border-radius: 6px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #8E9BAE; font-size: 14px; }}
        .accent {{ color: #C68642; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NordLayer</h1>
            <p>Мастерская цифрового ремесла из Карелии</p>
        </div>
        
        <div class="content">
            <h2>Здравствуйте, {customer_name}!</h2>
            
            <p>Статус вашего заказа изменился.</p>
            
            <div class="status-update">
                <h3>Новый статус заказа</h3>
                <span class="status">{status_text.upper()}</span>
            </div>
            
            <div class="order-info">
                <h3>Информация о заказе</h3>
                <p><strong>Номер заказа:</strong> <span class="accent">#{order_id}</span></p>
                <p><strong>Услуга:</strong> {service_name}</p>
            </div>
            
            <p>Если у вас есть вопросы по заказу, свяжитесь с нами.</p>
        </div>
        
        <div class="footer">
            <p><strong>NordLayer</strong><br>
            Мастерская цифрового ремесла из Карелии<br>
            <em>Слой за слоем рождается форма</em></p>
        </div>
    </div>
</body>
</html>
"""
    
    @staticmethod
    def status_change_text(order_data: Dict[str, Any]) -> str:
        """Plain text template for status change notification"""
        customer_name = order_data.get('customer_name', 'Уважаемый клиент')
        order_id = order_data.get('id', 'N/A')
        service_name = order_data.get('service_name', 'Не указана')
        status = order_data.get('status', 'unknown')
        
        status_messages = {
            "confirmed": "подтвержден и принят в работу",
            "in_progress": "выполняется",
            "ready": "готов к получению",
            "completed": "завершен",
            "cancelled": "отменен"
        }
        
        status_text = status_messages.get(status, f"изменен на: {status}")
        
        return f"""
Здравствуйте, {customer_name}!

Статус вашего заказа изменился.

ИНФОРМАЦИЯ О ЗАКАЗЕ:
• Номер заказа: #{order_id}
• Новый статус: {status_text.upper()}
• Услуга: {service_name}

Если у вас есть вопросы по заказу, свяжитесь с нами.

С уважением,
Команда NordLayer
Мастерская цифрового ремесла из Карелии

"Слой за слоем рождается форма"
"""