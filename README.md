# 3D Printing Platform - Backend API

FastAPI backend для платформы 3D печати.

## Технологии

- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **Pydantic** - валидация данных
- **SQLite/PostgreSQL** - база данных
- **Redis** - кеширование (опционально)
- **S3** - хранение файлов (опционально)

## Установка

### Требования

- Python 3.9+
- pip или poetry

### Шаги установки

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd backend
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. Инициализируйте базу данных:
```bash
python -m app.scripts.init_db
```

6. (Опционально) Заполните тестовыми данными:
```bash
python -m app.scripts.seed_data
```

## Запуск

### Режим разработки

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Продакшн

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Документация

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Конфигурация, безопасность
│   ├── crud/          # CRUD операции
│   ├── models/        # SQLAlchemy модели
│   ├── schemas/       # Pydantic схемы
│   ├── services/      # Бизнес-логика
│   └── scripts/       # Скрипты для инициализации
├── uploads/           # Загруженные файлы (локально)
├── .env.example       # Пример конфигурации
└── requirements.txt   # Python зависимости
```

## Конфигурация

### Обязательные переменные окружения

- `SECRET_KEY` - секретный ключ для JWT токенов
- `DATABASE_URL` - URL подключения к базе данных

### Опциональные переменные

- `USE_S3` - использовать S3 для хранения файлов (true/false)
- `REDIS_URL` - URL для подключения к Redis
- `ALLOWED_ORIGINS` - список разрешенных CORS origins

Полный список переменных см. в `.env.example`

## Тестирование

```bash
pytest
```

## Деплой

### Docker

```bash
docker build -t 3d-printing-backend .
docker run -p 8000:8000 --env-file .env 3d-printing-backend
```

### Без Docker

1. Установите зависимости
2. Настройте `.env` файл
3. Запустите с помощью gunicorn или uvicorn

## Безопасность

⚠️ **Важно:**
- Никогда не коммитьте `.env` файл
- Используйте сильные пароли и секретные ключи
- В продакшене используйте PostgreSQL вместо SQLite
- Настройте HTTPS
- Регулярно обновляйте зависимости

## Лицензия

Proprietary
