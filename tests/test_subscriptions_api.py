"""API de suscripciones (F6): crear, listar, borrar y validaciones."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from apps.api import main
from boe.core.db import get_session


@pytest_asyncio.fixture
async def client(session_factory):
    async def _override():
        async with session_factory() as session:
            yield session

    main.app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    main.app.dependency_overrides.clear()


async def test_create_list_delete(client):
    # Crear.
    resp = await client.post(
        "/v1/subscriptions",
        json={"email": "ana@example.com", "topic_slug": "subvencion"},
    )
    assert resp.status_code == 201
    sub = resp.json()
    assert sub["destination"] == "ana@example.com"  # email por defecto
    assert sub["active"] is True
    sub_id = sub["id"]

    # Listar por email.
    resp = await client.get("/v1/subscriptions", params={"email": "ana@example.com"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Borrar.
    resp = await client.delete(f"/v1/subscriptions/{sub_id}")
    assert resp.status_code == 204
    resp = await client.get("/v1/subscriptions", params={"email": "ana@example.com"})
    assert resp.json()["total"] == 0


async def test_requires_at_least_one_filter(client):
    resp = await client.post("/v1/subscriptions", json={"email": "x@example.com"})
    assert resp.status_code == 422


async def test_telegram_requires_destination(client):
    resp = await client.post(
        "/v1/subscriptions",
        json={"email": "x@example.com", "channel": "telegram", "topic_slug": "sanidad"},
    )
    assert resp.status_code == 422
