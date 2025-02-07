# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Pharmacy OCR API"
    DEBUG: bool = True  # Enable debug mode
    API_V1_STR: str = "/api/v1"
    
    # OCR Configuration
    TESSERACT_CMD: str = "tesseract"
    MIN_CONFIDENCE: float = 0.5
    
    # Image Processing
    MAX_IMAGE_SIZE: int = 4096
    SUPPORTED_FORMATS: list = ["image/jpeg", "image/png"]
    
    # API Configuration
    CORS_ORIGINS: list = ["*"]  # Allow all origins in development
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: list = ["*"]
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./pharmacy_ocr.db"  # Default SQLite database
    
    # Cache Configuration
    CACHE_TTL: int = 3600  # Cache TTL in seconds
    REDIS_URL: str = "redis://localhost:6379/0"  # Redis cache URL
    
    # Authentication
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        case_sensitive = True

settings = Settings()