from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field, HttpUrl

from . import __version__


class Settings(BaseSettings):
    service_name: str = Field("golden-service-python", env="SERVICE_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    otlp_endpoint: Optional[HttpUrl] = Field(None, env="OTLP_ENDPOINT")
    maintenance_mode: bool = Field(False, env="MAINTENANCE_MODE")
    request_timeout: int = Field(25, env="REQUEST_TIMEOUT")

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
