"""Tests de integración de la API v1 (F2): digest, search, chat y auth.

Contra Postgres real (fixture `session_factory`, se salta si no hay DB). El LLM
del chat se mockea; la búsqueda usa la columna generada `search_vector` real.
"""

from datetime import date

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from apps.api import main
from apps.api.routers import chat as chat_router
from boe.core.db import get_session
from boe.core.enums import Scope
from boe.core.models import Document, Summary, Topic

_FECHA = date(2024, 7, 9)


async def _seed(session_factory):
    async with session_factory() as s:
        ayudas = Topic(name="Subvención", slug="subvencion")
        s.add(ayudas)
        d1 = Document(
            boe_id="BOE-A-2024-0001",
            published_at=_FECHA,
            title="Orden de ayudas y subvenciones a autónomos en Galicia",
            full_text="El Gobierno aprueba ayudas para autónomos gallegos.",
            scope=Scope.NACIONAL,
            departamento="MINISTERIO DE HACIENDA",
            url_html="https://boe.es/1",
            topics=[ayudas],
        )
        d2 = Document(
            boe_id="BOE-A-2024-0002",
            published_at=_FECHA,
            title="Nombramiento de funcionario del Ministerio de Justicia",
            full_text="Se nombra a un alto cargo.",
            scope=Scope.OTRO,
            departamento="MINISTERIO DE JUSTICIA",
        )
        s.add_all([d1, d2])
        await s.flush()
        s.add(Summary(document_id=d1.id, short="Nuevas ayudas para autónomos.", model="x"))
        await s.commit()


@pytest_asyncio.fixture
async def client(session_factory):
    await _seed(session_factory)

    async def _override():
        async with session_factory() as session:
            yield session

    main.app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    main.app.dependency_overrides.clear()


async def test_digest_groups_and_highlights(client):
    resp = await client.get("/v1/digest/2024-07-09")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    # El nacional (con resumen) va primero en destacados.
    assert data["highlights"][0]["boe_id"] == "BOE-A-2024-0001"
    assert data["highlights"][0]["short"] == "Nuevas ayudas para autónomos."
    scopes = {g["scope"] for g in data["groups"]}
    assert scopes == {"nacional", "otro"}


async def test_search_fulltext(client):
    resp = await client.post("/v1/search", json={"query": "ayudas autónomos"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["results"][0]["document"]["boe_id"] == "BOE-A-2024-0001"
    assert "texto" in data["results"][0]["matched"]


async def test_search_with_filter(client):
    resp = await client.post(
        "/v1/search", json={"query": "", "departamento": "JUSTICIA"}
    )
    assert resp.status_code == 200
    ids = {r["document"]["boe_id"] for r in resp.json()["results"]}
    assert ids == {"BOE-A-2024-0002"}


async def test_topics_listing_with_counts(client):
    resp = await client.get("/v1/topics")
    assert resp.status_code == 200
    topics = {t["slug"]: t for t in resp.json()["topics"]}
    assert topics["subvencion"]["name"] == "Subvención"
    assert topics["subvencion"]["count"] == 1


async def test_search_filter_by_topic(client):
    resp = await client.post("/v1/search", json={"query": "", "topic": "subvencion"})
    assert resp.status_code == 200
    ids = {r["document"]["boe_id"] for r in resp.json()["results"]}
    assert ids == {"BOE-A-2024-0001"}


async def test_chat_requires_provider(client):
    # Sin proveedor LLM configurado → 503.
    resp = await client.post("/v1/chat", json={"message": "¿hay ayudas?"})
    assert resp.status_code == 503


async def test_chat_with_mocked_llm(client, monkeypatch):
    class _FakeRouter:
        has_provider = True

        async def complete(self, messages, **kwargs):
            # Debe haber recibido el contexto con el boe_id para citar.
            assert "BOE-A-2024-0001" in messages[-1]["content"]
            return "Sí, hay ayudas para autónomos [BOE-A-2024-0001]."

    monkeypatch.setattr(chat_router, "get_router", lambda: _FakeRouter())
    resp = await client.post("/v1/chat", json={"message": "ayudas autónomos"})
    assert resp.status_code == 200
    data = resp.json()
    assert "[BOE-A-2024-0001]" in data["answer"]
    assert any(c["boe_id"] == "BOE-A-2024-0001" for c in data["citations"])


async def test_api_key_enforced(client, monkeypatch):
    from boe.core.config import settings

    monkeypatch.setattr(settings, "api_keys", "secret-key")
    # Sin cabecera → 401.
    resp = await client.post("/v1/search", json={"query": "ayudas"})
    assert resp.status_code == 401
    # Con cabecera correcta → 200.
    resp = await client.post(
        "/v1/search", json={"query": "ayudas"}, headers={"X-API-Key": "secret-key"}
    )
    assert resp.status_code == 200
