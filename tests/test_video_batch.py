"""Render por lotes: selección de piezas pendientes y flujo con runner falso."""

from datetime import date
from pathlib import Path

from boe.content.video.batch import pending_posts, render_approved
from boe.core.enums import ContentChannel, ContentStatus, Scope
from boe.core.models import ContentPost, Document

_EXTRA = {
    "hook": "¿Sabías esto?",
    "points": ["p1", "p2"],
    "cta": "Sigue a AlertaBOE",
    "narration": "El Gobierno aprueba ayudas para autónomos.",
}


async def _seed(session_factory):
    async with session_factory() as s:
        d = Document(
            boe_id="BOE-A-2024-0001",
            published_at=date(2024, 7, 9),
            title="Ayudas a autónomos",
            scope=Scope.NACIONAL,
        )
        s.add(d)
        await s.flush()
        s.add_all(
            [
                # Aprobada sin asset → se renderiza.
                ContentPost(
                    document_id=d.id,
                    channel=ContentChannel.TIKTOK,
                    status=ContentStatus.APPROVED,
                    script="guion",
                    metrics={"extra": _EXTRA},
                ),
                # Borrador → no.
                ContentPost(
                    document_id=d.id,
                    channel=ContentChannel.TIKTOK,
                    status=ContentStatus.DRAFT,
                    metrics={"extra": _EXTRA},
                ),
                # Aprobada pero sin guion estructurado → se salta.
                ContentPost(
                    document_id=d.id,
                    channel=ContentChannel.TIKTOK,
                    status=ContentStatus.APPROVED,
                    metrics={},
                ),
                # LinkedIn → no es vídeo.
                ContentPost(
                    document_id=d.id,
                    channel=ContentChannel.LINKEDIN,
                    status=ContentStatus.APPROVED,
                    metrics={"extra": _EXTRA},
                ),
            ]
        )
        await s.commit()


async def test_pending_posts_filters(session_factory):
    await _seed(session_factory)
    async with session_factory() as s:
        posts = await pending_posts(s)
    # Las dos TikTok aprobadas sin asset (con y sin guion estructurado).
    assert len(posts) == 2


async def test_render_approved_with_fake_runner(session_factory, tmp_path):
    await _seed(session_factory)

    async def fake_runner(props_path: Path, out_path: Path) -> bool:
        # El runner de Remotion corre con otro cwd: las rutas DEBEN ser absolutas.
        assert props_path.is_absolute()
        assert out_path.is_absolute()
        assert props_path.exists()  # los assets se generaron antes del render
        out_path.write_bytes(b"mp4")
        return True

    result = await render_approved(
        tmp_path, session_factory=session_factory, runner=fake_runner
    )
    assert result["renderizados"] == 1
    assert result["sin_guion"] == 1
    assert result["fallidos"] == 0

    # El asset quedó registrado y no se re-renderiza en una segunda pasada.
    async with session_factory() as s:
        remaining = await pending_posts(s)
    assert len(remaining) == 1  # solo la que no tiene guion estructurado
