"""Configuración central del proyecto (pydantic-settings).

Reemplaza al antiguo `app/core/config.py`, que leía variables sueltas con
`os.getenv` sin validación. Aquí todo está tipado y con valores por defecto
razonables para desarrollo.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="before")
    @classmethod
    def _ignore_empty_env(cls, values: dict) -> dict:
        """Ignora variables de entorno vacías para usar el valor por defecto.

        En CI/hosts, un secreto no configurado llega como cadena vacía (""), lo
        que rompería campos tipados (p. ej. `smtp_port: int`). Aquí se descartan
        para que apliquen los defaults en su lugar.
        """
        if isinstance(values, dict):
            return {k: v for k, v in values.items() if not (isinstance(v, str) and v == "")}
        return values

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
    llm_fallback_provider: str | None = "openai"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # OpenRouter sigue soportado como proveedor alternativo si se configura.
    openrouter_api_key: str | None = None
    openrouter_model: str = "deepseek/deepseek-chat"

    # ─── Embeddings ──────────────────────────────────────────────────────────
    embeddings_model: str = "BAAI/bge-m3"
    embeddings_dim: int = 1024

    # ─── API pública ─────────────────────────────────────────────────────────
    api_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    log_level: str = "INFO"

    # API keys válidas (coma-separadas). Vacío = API abierta (solo desarrollo).
    api_keys: str = ""

    # Recuperación para el chat RAG.
    chat_top_k: int = 6

    # ─── Alertas (F6) ────────────────────────────────────────────────────────
    # Email (SMTP). Si falta config, el notificador email funciona en dry-run.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "AlertaBOE <no-reply@alertaboe.app>"
    # Telegram. Si falta el token, el notificador Telegram va en dry-run.
    telegram_bot_token: str | None = None

    # URL pública de la web (para enlaces en emails y tarjetas).
    web_base_url: str = "https://alertaboe.vercel.app"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    @property
    def api_keys_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}

    @property
    def sync_database_url(self) -> str:
        """URL síncrona para Alembic (psycopg).

        Quita el parámetro `ssl` de la query si lo hubiera: es de asyncpg;
        psycopg negocia SSL solo (sslmode=prefer) y no entiende `ssl`.
        """
        from sqlalchemy.engine.url import make_url

        url = make_url(self.database_url)
        # Cualquier URL de Postgres (postgresql://, +asyncpg, postgres://) usa
        # psycopg v3 para Alembic (psycopg2 no está instalado).
        if url.get_backend_name() == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        if "ssl" in url.query:
            url = url.difference_update_query(["ssl"])
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
