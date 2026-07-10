"""API de la cola de contenido: listar, aprobar, rechazar y publicar."""

from datetime import date

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from apps.api import main
from boe.core.db import get_session
from boe.core.enums import ContentChannel, ContentStatus, Scope
from boe.core.models import ContentPost, Document


async def _seed(session_factory) -> int:
    async with session_factory() as s:
        d = Document(
            boe_id="BOE-A-2024-0001",
            published_at=date(2024, 7, 9),
            title="Orden de ayudas a autónomos",
            scope=Scope.NACIONAL,
        )
        s.add(d)
        await s.flush()
        post = ContentPost(
            document_id=d.id,
            channel=ContentChannel.LINKEDIN,
            status=ContentStatus.DRAFT,
            script="Post divulgativo. Fuente [BOE-A-2024-0001].",
            interest_score=0.8,
        )
        s.add(post)
        await s.flush()
        pid = post.id
        await s.commit()
        return pid


@pytest_asyncio.fixture
async def client(session_factory):
    post_id = await _seed(session_factory)

    async def _override():
        async with session_factory() as session:
            yield session

    main.app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, post_id
    main.app.dependency_overrides.clear()


async def test_list_and_approve_publish_flow(client):
    c, post_id = client

    # Listado de borradores.
    resp = await c.get("/v1/content", params={"status": "draft"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["posts"][0]["boe_id"] == "BOE-A-2024-0001"

    # No se puede publicar un borrador sin aprobar.
    resp = await c.post(f"/v1/content/{post_id}/publish")
    assert resp.status_code == 409

    # Aprobar → publicar (dry-run).
    resp = await c.post(f"/v1/content/{post_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    resp = await c.post(f"/v1/content/{post_id}/publish")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "published"
    assert body["external_id"] == "dryrun-linkedin"
    assert body["published_at"] is not None


async def test_reject(client):
    c, post_id = client
    resp = await c.post(f"/v1/content/{post_id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
