"""Integración del pipeline de contenido contra DB, con LLM mockeado."""

from datetime import date

from sqlalchemy import select

from boe.content.pipeline import ContentPipeline
from boe.core.enums import ContentChannel, ContentStatus, Scope
from boe.core.models import ContentPost, Document, Summary, Topic
from tests.content_fakes import FakeContentRouter

_FECHA = date(2024, 7, 9)


async def _seed(session_factory):
    async with session_factory() as s:
        t = Topic(name="Subvención", slug="subvencion")
        d = Document(
            boe_id="BOE-A-2024-0001",
            published_at=_FECHA,
            title="Orden de ayudas a autónomos",
            rango="Orden",
            scope=Scope.NACIONAL,
        )
        d.topics.append(t)
        s.add(d)
        await s.flush()
        s.add(Summary(document_id=d.id, long="Ayudas para autónomos.", short="Ayudas.", model="x"))
        await s.commit()


async def test_pipeline_creates_validated_drafts(session_factory):
    await _seed(session_factory)
    pipeline = ContentPipeline(session_factory=session_factory, router=FakeContentRouter())

    ids = await pipeline.generate_for_date(_FECHA, top_n=1)
    # 3 canales por documento.
    assert len(ids) == 3

    async with session_factory() as s:
        posts = (await s.execute(select(ContentPost))).scalars().all()
        assert {p.channel for p in posts} == {
            ContentChannel.LINKEDIN, ContentChannel.X, ContentChannel.TIKTOK
        }
        assert all(p.status == ContentStatus.DRAFT for p in posts)
        # El validador pasó y la cita a la fuente está.
        for p in posts:
            assert p.metrics["validation"]["ok"] is True
            assert "BOE-A-2024-0001" in p.script
            assert p.interest_score is not None
        # El guion de TikTok guarda la estructura para el vídeo.
        tiktok = next(p for p in posts if p.channel == ContentChannel.TIKTOK)
        assert "narration" in tiktok.metrics["extra"]


async def test_pipeline_is_idempotent(session_factory):
    await _seed(session_factory)
    pipeline = ContentPipeline(session_factory=session_factory, router=FakeContentRouter())

    await pipeline.generate_for_date(_FECHA, top_n=1)
    second = await pipeline.generate_for_date(_FECHA, top_n=1)
    assert second == []  # ya existían borradores para esos canales

    async with session_factory() as s:
        n = len((await s.execute(select(ContentPost))).scalars().all())
    assert n == 3
