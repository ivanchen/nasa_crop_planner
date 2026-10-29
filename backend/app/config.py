from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    earthdata_username: str = ""
    earthdata_password: str = ""
    cors_origins: str = "http://localhost:5173"
    cache_ttl_seconds: int = 86400
    default_years: int = 5
    job_timeout_seconds: int = 900
    google_ai_studio_api_key: str = ""
    google_ai_studio_model: str = "gemini-2.5-flash"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def earthdata_configured(self) -> bool:
        return bool(self.earthdata_username and self.earthdata_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
