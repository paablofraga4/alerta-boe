"""Pipeline de la fábrica de contenido: curar → guionizar → validar → encolar.

Selecciona las publicaciones más interesantes de un día, genera piezas por canal,
las valida y las deja como BORRADOR en `content_posts` para aprobación humana.
No publica: la publicación es un paso posterior y con confirmación.
"""

from __future__ import annotations

from datetime import date

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from boe.content import writer
from boe.content.curator import CandidateSignals, rank
from boe.content.validator import validate
from boe.core.db import SessionLocal
from boe.core.enums import ContentChannel, ContentStatus
from boe.core.models import ContentPost, Document, Reference
from boe.llm.router import LLMRouter, get_router

log = structlog.get_logger(__name__)

DEFAULT_CHANNELS = [ContentChannel.LINKEDIN, ContentChannel.X, ContentChannel.TIKTOK]


async def _signals_for(session: AsyncSession, doc: Document) -> CandidateSignals:
    n_refs = (
        await session.execute(
            select(func.count(Reference.id)).where(Reference.source_id == doc.id)
        )
    ).scalar_one()
    return CandidateSignals(
        boe_id=doc.boe_id,
        scope=doc.scope,
        rango=doc.rango,
        topics=[t.name for t in doc.topics],
        n_references=n_refs,
        has_summary=bool(doc.summaries),
    )


def _resumen(doc: Document) -> str:
    if doc.summaries:
        s = doc.summaries[0]
        return s.long or s.short or doc.title
    return doc.title


async def _existing_channels(
    session: AsyncSession, document_id: int
) -> set[ContentChannel]:
    rows = (
        await session.execute(
            select(ContentPost.channel).where(
                ContentPost.document_id == document_id,
                ContentPost.status != ContentStatus.REJECTED,
            )
        )
    ).scalars().all()
    return set(rows)


class ContentPipeline:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
        router: LLMRouter | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._router = router if router is not None else get_router()

    async def generate_for_date(
        self,
        fecha: date,
        *,
        top_n: int = 3,
        channels: list[ContentChannel] | None = None,
    ) -> list[int]:
        """Genera borradores para las mejores publicaciones del día. IDs creados."""
        if not self._router.has_provider:
            raise RuntimeError("No hay proveedor LLM configurado para generar contenido.")

        channels = channels or DEFAULT_CHANNELS
        created: list[int] = []

        async with self._session_factory() as session:
            docs = (
                await session.execute(
                    select(Document)
                    .where(Document.published_at == fecha)
                    .options(selectinload(Document.summaries), selectinload(Document.topics))
                )
            ).scalars().all()
            if not docs:
                return created

            signals = [await _signals_for(session, d) for d in docs]
            by_id = {d.boe_id: d for d in docs}
            selected = rank(signals, top_n=top_n)

            for cand, interest in selected:
                doc = by_id[cand.boe_id]
                resumen = _resumen(doc)
                already = await _existing_channels(session, doc.id)

                for channel in channels:
                    if channel in already:
                        continue
                    try:
                        text, extra = await writer.write(
                            self._router, channel,
                            titulo=doc.title, resumen=resumen, boe_id=doc.boe_id,
                        )
                        result = await validate(
                            self._router, channel, text,
                            titulo=doc.title, resumen=resumen, boe_id=doc.boe_id,
                        )
                    except Exception as exc:  # noqa: BLE001
                        log.warning("content_generation_failed",
                                    boe_id=doc.boe_id, channel=channel.value, error=str(exc))
                        continue

                    post = ContentPost(
                        document_id=doc.id,
                        channel=channel,
                        status=ContentStatus.DRAFT,
                        script=text,
                        interest_score=interest,
                        metrics={"validation": result.model_dump(), "extra": extra},
                    )
                    session.add(post)
                    await session.flush()
                    created.append(post.id)

            await session.commit()

        log.info("content_generated", fecha=str(fecha), borradores=len(created))
        return created
