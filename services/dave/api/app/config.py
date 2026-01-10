from functools import lru_cache
from typing import Optional

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings

from . import __version__


class Settings(BaseSettings):
    service_name: str = Field("dave", env="SERVICE_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    otlp_endpoint: Optional[HttpUrl] = Field(None, env="OTLP_ENDPOINT")
    maintenance_mode: bool = Field(False, env="MAINTENANCE_MODE")
    request_timeout: int = Field(25, env="REQUEST_TIMEOUT")

    # Supabase
    supabase_url: Optional[str] = Field(None, env="SUPABASE_URL")
    supabase_service_key: Optional[str] = Field(None, env="SUPABASE_SERVICE_KEY")

    # Authentication
    dave_api_key: Optional[str] = Field(None, env="DAVE_API_KEY")
    admin_api_key: Optional[str] = Field(None, env="ADMIN_API_KEY")

    # Gemini AI
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-1.5-flash", env="GEMINI_MODEL")
    gemini_embedding_model: str = Field("models/text-embedding-004", env="GEMINI_EMBEDDING_MODEL")

    # Rate limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")

    # Caching
    cache_ttl_prompts: int = Field(300, env="CACHE_TTL_PROMPTS")  # 5 minutes default

    @property
    def app_version(self) -> str:
        """Get application version."""
        return __version__

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
