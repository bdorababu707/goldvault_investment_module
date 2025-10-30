import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
load_dotenv()


class Jwt(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = os.getenv("VERIFICATION_TOKEN_EXPIRE_MINUTES")

class DatabaseTables(BaseModel):
    ADMINS: str = os.getenv("ADMINS")
    USERS: str = os.getenv("USERS")
    AVAILABLE_INVESTMENT_PLANS: str = os.getenv("AVAILABLE_INVESTMENT_PLANS")
    SUBSCRIPTIONS: str = os.getenv("SUBSCRIPTIONS")
    INVENTORY: str = os.getenv("INVENTORY")
    INVESTMENT_ENTRIES: str = os.getenv("INVESTMENT_ENTRIES")

class DatabaseConfig(BaseModel):
    URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "goldvault_investments"
    MAX_POOL_SIZE: int = 10
    MIN_POOL_SIZE: int = 1
    MAX_IDLE_TIME_MS: int = 30000
    SERVER_SELECTION_TIMEOUT_MS: int = 5000
    CONNECT_TIMEOUT_MS: int = 10000

class ServerConfig(BaseModel):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False  # Set to True for development, False for production
    RELOAD: bool = False

class SMTPConfig(BaseModel):
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASS: str = os.getenv("SMTP_PASS")
    SMTP_FROM: str = os.getenv("SMTP_FROM")

class S3Credentials(BaseModel):
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME")
    ALLOWED_FILE_EXTENSIONS: str = os.getenv("ALLOWED_FILE_EXTENSIONS")
    MAX_FILE_SIZE_MB: int = os.getenv("MAX_FILE_SIZE_MB")
    BASE_DIR: str = os.getenv("BASE_DIR")
    MAX_CONCURRENT_UPLOADS: int = os.getenv("MAX_CONCURRENT_UPLOADS")

class SecretKeys(BaseModel):
    SUPER_ADMIN_SECRET_KEY: str = os.getenv("SUPER_ADMIN_SECRET_KEY")

class AppConfig(BaseModel):
    TITLE: str = "FastAPI MongoDB Service"
    DESCRIPTION: str = "FastAPI service with MongoDB integration"
    VERSION: str = "1.0.0"
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

class LoggingConfig(BaseModel):
    LEVEL: str = "info"
    FILE_PATH: str = "../logs"
    ROTATION_SIZE_MB: int = 10
    BACKUP_COUNT: int = 5
    
    @field_validator('LEVEL')
    def validate_log_level(cls, v):
        allowed_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.lower()

class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    
    # Nested configuration
    DB: DatabaseConfig = DatabaseConfig()
    SERVER: ServerConfig = ServerConfig()
    APP: AppConfig = AppConfig()
    LOG: LoggingConfig = LoggingConfig()
    JWT: Jwt = Jwt()
    DB_TABLE: DatabaseTables = DatabaseTables()
    S3_CREDENTIALS: S3Credentials = S3Credentials()
    SECRET_KEYS: SecretKeys = SecretKeys()
    SMTP: SMTPConfig = SMTPConfig()
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='ignore'
    )
    
    @model_validator(mode='after')
    def set_environment_settings(self) -> 'Settings':
        """Set appropriate settings based on environment"""
        # Set DEBUG mode based on environment
        if self.ENV.lower() == "development":
            self.SERVER.DEBUG = True
            self.SERVER.RELOAD = True
            if self.LOG.LEVEL == "info":  # Only override if not explicitly set
                self.LOG.LEVEL = "debug"
        elif self.ENV.lower() == "production":
            self.SERVER.DEBUG = False
            self.SERVER.RELOAD = False
            if self.LOG.LEVEL == "debug":  # In production, minimum level is info
                self.LOG.LEVEL = "info"
        
        # Ensure log directory exists
        log_dir = Path(self.LOG.FILE_PATH)
        log_dir.mkdir(exist_ok=True)
        
        return self
    
    def is_development(self) -> bool:
        """Helper method to check if running in development mode"""
        return self.SERVER.DEBUG
    
    def get_log_level(self) -> int:
        """Convert string log level to logging module constant"""
        import logging
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        return level_map.get(self.LOG.LEVEL, logging.INFO)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# For direct imports
settings = get_settings()