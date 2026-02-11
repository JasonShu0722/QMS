"""
配置管理模块
读取环境变量并提供全局配置对象
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    系统全局配置
    使用 Pydantic Settings 自动从环境变量读取配置
    """
    
    # 应用基础配置
    APP_NAME: str = "QMS Quality Management System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "stable"  # stable or preview
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://qms_user:password@localhost:5432/qms_db"
    DB_ECHO: bool = False  # SQLAlchemy 日志
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # 密码策略配置
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_EXPIRE_DAYS: int = 90
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    
    # LDAP 配置（预留 SSO 集成）
    LDAP_SERVER: Optional[str] = None
    LDAP_BASE_DN: Optional[str] = None
    LDAP_BIND_DN: Optional[str] = None
    LDAP_BIND_PASSWORD: Optional[str] = None
    LDAP_ENABLED: bool = False
    
    # IMS 系统集成配置
    IMS_BASE_URL: Optional[str] = None
    IMS_API_KEY: Optional[str] = None
    IMS_TIMEOUT: int = 30  # 秒
    
    # SMTP 邮件配置
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Celery 任务队列配置
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # CORS 配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # OpenAI API 配置（AI 诊断功能）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None  # 支持 DeepSeek 等兼容接口
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 创建全局配置实例
settings = Settings()
