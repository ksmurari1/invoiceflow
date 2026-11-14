"""Application settings loaded from environment variables (and backend/.env)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration. Secrets have no defaults; they come from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENV: Literal["development", "test", "production"] = "development"
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)
    FRONTEND_URL: str = "http://localhost:5173"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # Local MVP: no login. Every request acts as this seeded demo user (see app/auth).
    DEMO_USER_ID: int = Field(default=1, ge=1)


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings.

    Returns:
        Settings instance built from environment variables and backend/.env.
    """
    return Settings()
