from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VoxAgent MVP"
    app_env: str = "local"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = Field(default="change-me")
    api_base_url: str = "http://api:8000"
    web_port: int = 3000

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "voxagent"
    postgres_user: str = "voxagent"
    postgres_password: str = "voxagent_password"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    default_language: str = "bn-BD"
    secondary_language: str = "en-US"
    supported_languages: str = "bn-BD,en-US"
    default_stt_provider: str = "groq"
    default_llm_provider: str = "claude"
    default_tts_provider: str = "cartesia"
    stt_timeout_seconds: float = 30
    llm_timeout_seconds: float = 45
    tts_timeout_seconds: float = 30
    provider_retry_attempts: int = 2
    llm_temperature: float = 0.3
    llm_max_tokens: int = 450
    default_tts_voice: str | None = None
    groq_api_key: str | None = None
    groq_stt_model: str = "whisper-large-v3-turbo"
    groq_llm_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    cartesia_api_key: str | None = None
    cartesia_model: str = "sonic-3.5"
    cartesia_version: str = "2026-03-01"
    cartesia_voice_id: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6"
    openai_tts_model: str = "gpt-4o-mini-tts-2025-12-15"
    deepgram_api_key: str | None = None
    assemblyai_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    rate_limit_per_minute: int = 120
    jwt_issuer: str = "voxagent-local"
    jwt_audience: str = "voxagent-api"
    jwt_algorithm: str = "HS256"
    demo_admin_email: str = "admin@voxagent.local"
    demo_admin_password: str = "admin123"
    demo_jwt_expires_minutes: int = 480
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def languages(self) -> list[str]:
        return [language.strip() for language in self.supported_languages.split(",") if language.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
