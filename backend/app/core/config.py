from typing import List, Union, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    APP_NAME: str = Field(default="women-safety-backend", description="Name of the application")
    APP_ENV: str = Field(default="development", description="Environment mode")
    DEBUG: bool = Field(default=True, description="Debug flag")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 route prefix")

    SUPABASE_URL: str = Field(
        default="https://your-project.supabase.co",
        description="Supabase Project Base URL"
    )
    SUPABASE_ANON_KEY: str = Field(
        default="your-anon-key",
        description="Supabase Public Anon Key"
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="your-service-role-key",
        description="Supabase Service Role Key (Server-side only)"
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/postgres",
        description="SQLAlchemy PostgreSQL connection string for Supabase"
    )

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery message broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result storage backend URL"
    )

    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
