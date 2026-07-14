"""Motor y sesiones async de SQLAlchemy 2.

Sustituye al `app/db/session.py` síncrono. Todo el I/O de base de datos del
producto nuevo es async, en coherencia con FastAPI y con los clientes httpx.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from boe.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos."""


def _build_engine():
    """Crea el engine async, activando SSL para hosts gestionados (Supabase).

    asyncpg no usa SSL por defecto y Supabase lo exige, así que se activa cuando
    el host es de Supabase o la URL trae `?ssl=require`. El parámetro `ssl` se
    saca de la query (asyncpg lo recibe por connect_args, no por la URL).
    """
    url = make_url(settings.database_url)

    # Fuerza el driver async. Aunque la DATABASE_URL venga como `postgresql://`
    # (lo que da Supabase por defecto), usamos asyncpg — si no, SQLAlchemy
    # intentaría psycopg2 (no instalado) y fallaría.
    if url.get_backend_name() == "postgresql" and url.get_driver_name() != "asyncpg":
        url = url.set(drivername="postgresql+asyncpg")

    host = url.host or ""
    ssl_flag = str(url.query.get("ssl", "")).lower()
    wants_ssl = ssl_flag in {"require", "true", "1"} or "supabase" in host

    if "ssl" in url.query:
        url = url.difference_update_query(["ssl"])

    connect_args: dict = {}
    if wants_ssl:
        # Cifra pero NO verifica el certificado (equivale a sslmode=require, el
        # modo estándar con Supabase). Su pooler presenta un cert que no valida
        # contra el almacén de CAs por defecto → 'ssl=True' fallaría.
        import ssl as _ssl

        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        connect_args["ssl"] = ctx

    return create_async_engine(
        url, echo=settings.db_echo, pool_pre_ping=True, connect_args=connect_args
    )


engine = _build_engine()

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia FastAPI: una sesión por request."""
    async with SessionLocal() as session:
        yield session
