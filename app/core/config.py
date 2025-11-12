from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./printing_platform.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File uploads
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: list = [".stl", ".obj", ".3mf", ".jpg", ".jpeg", ".png"]
    
    # S3 Configuration
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "3d-printing-platform"
    s3_region: str = "ru-central1"
    s3_endpoint_url: str = "https://storage.yandexcloud.net"
    use_s3: bool = False  # Disabled by default for development
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # CORS
    allowed_origins: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173"
    ]
    
    # Email Notifications
    email_notifications_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@nordlayer.com"
    
    # Telegram Notifications
    telegram_bot_webhook_url: str = ""
    telegram_admin_chat_ids: str = ""  # Comma-separated list
    
    @property
    def telegram_admin_chat_ids_list(self) -> list:
        """Convert comma-separated admin chat IDs to list of integers"""
        if not self.telegram_admin_chat_ids:
            return []
        try:
            return [int(chat_id.strip()) for chat_id in self.telegram_admin_chat_ids.split(",") if chat_id.strip()]
        except ValueError:
            return []
    
    class Config:
        env_file = ".env"

settings = Settings()