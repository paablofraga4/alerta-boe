"""Configuración central del proyecto (pydantic-settings).

Reemplaza al antiguo `app/core/config.py`, que leía variables sueltas con
`os.getenv` sin validación. Aquí todo está tipado y con valores por defecto
razonables para desarrollo.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ─── Base de datos ───────────────────────────────────────────────────────
    # Debe ser una URL async (postgresql+asyncpg://...).
    database_url: str = Field(
        default="postgresql+asyncpg://alertaboe:alertaboe@localhost:5432/alertaboe"
    )
    db_echo: bool = False

    # ─── APIs del BOE ────────────────────────────────────────────────────────
    boe_api_base: str = "https://boe.es/datosabiertos/api"
    boe_request_timeout: float = 30.0
    boe_max_retries: int = 4

    # ─── LLM ─────────────────────────────────────────────────────────────────
    llm_primary_provider: str = "groq"
    llm_fallback_provider: str | None = "openrouter"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    openrouter_api_key: str | None = None
    openrouter_model: str = "deepseek/deepseek-chat"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # ─── Embeddings ──────────────────────────────────────────────────────────
    embeddings_model: str = "BAAI/bge-m3"
    embeddings_dim: int = 1024

    # ─── API pública ─────────────────────────────────────────────────────────
    api_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    @property
    def sync_database_url(self) -> str:
        """URL síncrona para Alembic (psycopg)."""
        return self.database_url.replace("+asyncpg", "+psycopg").replace(
            "postgresql://", "postgresql+psycopg://"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
