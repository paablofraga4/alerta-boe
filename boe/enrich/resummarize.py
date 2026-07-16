"""Backfill de resúmenes al agente v2 (brief estructurado).

Los documentos ingeridos antes de desplegar el agente por noticia tienen un
resumen v1 (solo long/short/hook, sin `structured`). Sin `structured.plazos` el
Radar de plazos y la ficha rica quedan vacíos. Este módulo regenera esos
resúmenes con el agente que lee el texto completo, actualizando la fila
existente in situ. Es idempotente: solo toca lo que aún no es v2.
"""

from __future__ import annotations

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from boe.core.db import SessionLocal
from boe.core.models import Document, Summary
from boe.enrich.document_agent import summarize_document
from boe.llm.prompts import PROMPT_VERSION
from boe.llm.router import LLMRouter, get_router

log = structlog.get_logger(__name__)


async def _pending(session: AsyncSession, limit: int, since=None) -> list[Summary]:
    """Resúmenes que aún no son v2 (o sin brief estructurado), más recientes
    primero para que el Radar se pueble antes con lo que más importa."""
    stmt = (
        select(Summary)
        .join(Document, Document.id == Summary.document_id)
        .where(or_(Summary.prompt_version != PROMPT_VERSION, Summary.structured.is_(None)))
        .order_by(Document.published_at.desc(), Summary.id.desc())
        .limit(limit)
    )
    if since is not None:
        stmt = stmt.where(Document.published_at >= since)
    return list((await session.execute(stmt)).scalars().all())


async def resummarize_pending(
    *,
    limit: int = 100,
    since=None,
    router: LLMRouter | None = None,
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
) -> dict[str, int]:
    """Regenera al agente v2 los resúmenes pendientes. Devuelve contadores."""
    router = router or get_router()
    if not router.has_provider:
        return {"actualizados": 0, "fallidos": 0, "pendientes": 0, "sin_llm": 1}

    updated = failed = 0
    async with session_factory() as session:
        pendientes = await _pending(session, limit, since)
        for summary in pendientes:
            doc = await session.get(Document, summary.document_id)
            if doc is None:
                continue
            try:
                brief, version = await summarize_document(
                    router, doc.full_text or "", doc.title
                )
            except Exception as exc:  # noqa: BLE001 — un fallo no tumba el lote
                failed += 1
                log.warning("resummarize_failed", boe_id=doc.boe_id, error=str(exc))
                continue
            summary.long = brief.long
            summary.short = brief.short
            summary.hook = brief.hook
            summary.structured = brief.model_dump(exclude={"long", "short", "hook"})
            summary.model = "llm"
            summary.prompt_version = version
            updated += 1
        await session.commit()

    log.info("resummarize_done", actualizados=updated, fallidos=failed)
    return {"actualizados": updated, "fallidos": failed, "pendientes": len(pendientes)}
