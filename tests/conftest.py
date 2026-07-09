import json
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from boe.core import models  # noqa: F401 — registra las tablas
from boe.core.config import settings
from boe.core.db import Base

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def sumario() -> dict:
    return load_fixture("sumario.json")


@pytest.fixture
def analisis() -> dict:
    return load_fixture("analisis.json")


@pytest.fixture
def metadatos() -> dict:
    return load_fixture("metadatos.json")


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker:
    """Sesión async contra un Postgres+pgvector real.

    Si no hay DB disponible (p. ej. el job de tests sin servicio de Postgres),
    el test se salta en vez de fallar. El job de integración del CI sí la provee.
    """
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        await engine.dispose()
        pytest.skip("No hay Postgres disponible para tests de integración")

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # Limpia entre tests para aislarlos.
        await conn.execute(
            text(
                "TRUNCATE documents, \"references\", summaries, embeddings, "
                "topics, regions, pipeline_state, document_topics, "
                "document_regions, content_posts, document_versions "
                "RESTART IDENTITY CASCADE"
            )
        )

    yield async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()
