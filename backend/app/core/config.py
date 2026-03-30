"""
Configuration management for the QMS backend.
"""

import json
from typing import Optional

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "QMS Quality Management System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "stable"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://qms_user:password@localhost:5432/qms_db"
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_EXPIRE_DAYS: int = 90
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30

    LDAP_SERVER: Optional[str] = None
    LDAP_BASE_DN: Optional[str] = None
    LDAP_BIND_DN: Optional[str] = None
    LDAP_BIND_PASSWORD: Optional[str] = None
    LDAP_ENABLED: bool = False

    IMS_BASE_URL: Optional[str] = None
    IMS_API_KEY: Optional[str] = None
    IMS_TIMEOUT: int = 30

    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True

    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        validation_alias=AliasChoices("CORS_ORIGINS", "BACKEND_CORS_ORIGINS"),
    )

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                return json.loads(raw)
            return [item.strip() for item in raw.split(",") if item.strip()]

        return value


settings = Settings()
