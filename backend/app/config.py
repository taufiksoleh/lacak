from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./lacak.db"
    cors_origins: str = "http://localhost:5173"
    timezone: str = "Asia/Jakarta"

    # Konektor platform (semuanya opsional; konektor tanpa kredensial dinonaktifkan)
    youtube_api_key: str = ""
    x_bearer_token: str = ""
    meta_access_token: str = ""
    ig_business_account_id: str = ""
    threads_access_token: str = ""
    graph_api_version: str = "v21.0"

    # AI (Claude) - opsional; tanpa key, analisis tetap jalan dengan aturan (rule-based)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"
    ai_web_search_max_uses: int = 8

    activity_limit: int = 200

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
