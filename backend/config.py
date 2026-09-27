"""
Configuration settings for Shapir Recordings System
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    API_TITLE: str = "Shapir Recordings API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # OpenAI Configuration
    OPENAI_API_KEY: str  # Required - must be set in environment
    OPENAI_MODEL_SUMMARY: str = "gpt-4-turbo-preview"
    OPENAI_MODEL_WHISPER: str = "whisper-1"

    # Database Configuration
    DATABASE_URL: str  # SQL Server connection string
    # Example: "mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"

    # Authentication
    AD_SERVER: str = "ldap://localhost:389"  # Windows AD LDAP server
    AD_BASE_DN: str = "dc=shapir,dc=local"  # Base distinguished name
    AD_BIND_DN: Optional[str] = None  # Service account (if required)
    AD_BIND_PASSWORD: Optional[str] = None  # Service account password

    # File Storage
    UPLOAD_DIR: str = "./uploads"  # Local directory for audio files
    MAX_FILE_SIZE_MB: int = 100  # Maximum file size in MB
    ALLOWED_EXTENSIONS: list = ["mp3", "m4a", "wav", "ogg", "webm"]

    # Session Configuration
    SESSION_SECRET_KEY: str  # Used for session signing
    SESSION_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Retention Policy
    RETENTION_DAYS: int = 30  # Days to keep recordings

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # CORS (for React frontend)
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
