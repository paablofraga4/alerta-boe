"""Motor y sesiones async de SQLAlchemy 2.

Sustituye al `app/db/session.py` síncrono. Todo el I/O de base de datos del
producto nuevo es async, en coherencia con FastAPI y con los clientes httpx.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from boe.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos."""


engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia FastAPI: una sesión por request."""
    async with SessionLocal() as session:
        yield session
