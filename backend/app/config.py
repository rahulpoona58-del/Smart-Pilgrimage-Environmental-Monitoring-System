# backend/app/config.py
# Configuration Management: Loads environment variables using Pydantic Settings.

import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Smart Pilgrimage Environmental Monitoring System (SPEMS)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    # Falls back to local SQLite database if Postgres is not configured
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://admin:password123@spems_postgres:5432/smart_pilgrimage_db",
        env="DATABASE_URL"
    )
    
    # Security & Tokens
    SPEMS_DRONE_AUTH_TOKEN: str = Field("drone-cloud-key-999", env="SPEMS_DRONE_AUTH_TOKEN")
    SECRET_KEY: str = Field("super-secret-jwt-signing-key-12345", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Storage
    STATIC_UPLOAD_DIR: str = "static/evidence"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instantiate single settings context
settings = Settings()
