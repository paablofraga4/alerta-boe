"""Acceso a datos de la ingesta: upsert de documentos y estado del pipeline.

Aísla todas las escrituras/consultas de DB del pipeline, para que el runner
(`pipeline.py`) quede legible y la lógica de "qué documentos están listos para
la etapa X" viva en un solo sitio.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from boe.clients.dto import SummaryItem
from boe.core.enums import PipelineStage, StageStatus
from boe.core.models import Document, PipelineState, Region, Topic
from boe.enrich.triage import triage

# Secciones cuyo contenido se consolida (habilita el grafo normativo).
_CONSOLIDABLE_SECTIONS = {"1"}  # I. Disposiciones generales


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("ó", "o").replace("í", "i")


async def upsert_document(
    session: AsyncSession, item: SummaryItem, published_at: date
) -> tuple[Document, bool]:
    """Crea el documento si no existe (idempotente por boe_id). (doc, creado)."""
    existing = await session.execute(
        select(Document).where(Document.boe_id == item.boe_id)
    )
    doc = existing.scalar_one_or_none()
    if doc is not None:
        return doc, False

    consolidated_id = (
        item.boe_id if item.seccion_codigo in _CONSOLIDABLE_SECTIONS else None
    )
    tri = triage(
        title=item.title,
        seccion_codigo=item.seccion_codigo,
        epigrafe=item.epigrafe,
    )
    doc = Document(
        boe_id=item.boe_id,
        published_at=published_at,
        title=item.title,
        seccion=item.seccion,
        seccion_codigo=item.seccion_codigo,
        departamento=item.departamento,
        epigrafe=item.epigrafe,
        url_html=item.url_html,
        url_pdf=item.url_pdf,
        url_xml=item.url_xml,
        pages=item.pages,
        consolidated_id=consolidated_id,
        category=tri.category,
        relevance=tri.relevance,
    )
    session.add(doc)
    await session.flush()
    return doc, True


async def set_stage(
    session: AsyncSession,
    document_id: int,
    stage: PipelineStage,
    status: StageStatus,
    *,
    error: str | None = None,
    bump_attempt: bool = False,
) -> None:
    """Crea o actualiza el estado de una etapa para un documento."""
    existing = await session.execute(
        select(PipelineState).where(
            PipelineState.document_id == document_id, PipelineState.stage == stage
        )
    )
    row = existing.scalar_one_or_none()
    if row is None:
        row = PipelineState(document_id=document_id, stage=stage)
        session.add(row)
    row.status = status
    row.error = error
    if bump_attempt:
        row.attempts = (row.attempts or 0) + 1
    await session.flush()


async def attach_regions(
    session: AsyncSession, doc: Document, region_names: list[str]
) -> None:
    for name in region_names:
        result = await session.execute(select(Region).where(Region.name == name))
        region = result.scalar_one_or_none()
        if region is None:
            region = Region(name=name)
            session.add(region)
            await session.flush()
        if region not in doc.regions:
            doc.regions.append(region)


async def attach_topics(
    session: AsyncSession, doc: Document, topic_names: list[str]
) -> None:
    for name in topic_names:
        result = await session.execute(select(Topic).where(Topic.name == name))
        topic = result.scalar_one_or_none()
        if topic is None:
            topic = Topic(name=name, slug=_slug(name))
            session.add(topic)
            await session.flush()
        if topic not in doc.topics:
            doc.topics.append(topic)


async def documents_ready_for(
    session: AsyncSession,
    stage: PipelineStage,
    predecessor: PipelineStage | None,
    *,
    limit: int,
    max_attempts: int,
    require_consolidated: bool = False,
) -> list[Document]:
    """Documentos listos para la etapa `stage`.

    Un documento está listo si su etapa predecesora está DONE y esta etapa no
    está ya DONE ni ha agotado sus reintentos (FAILED con attempts >= max).
    """
    done_here = (
        select(PipelineState.document_id)
        .where(PipelineState.stage == stage, PipelineState.status == StageStatus.DONE)
    )
    exhausted = (
        select(PipelineState.document_id)
        .where(
            PipelineState.stage == stage,
            PipelineState.status == StageStatus.FAILED,
            PipelineState.attempts >= max_attempts,
        )
    )
    skipped = (
        select(PipelineState.document_id)
        .where(PipelineState.stage == stage, PipelineState.status == StageStatus.SKIPPED)
    )

    stmt = select(Document)
    if predecessor is not None:
        prev_done = (
            select(PipelineState.document_id).where(
                PipelineState.stage == predecessor,
                PipelineState.status == StageStatus.DONE,
            )
        )
        stmt = stmt.where(Document.id.in_(prev_done))

    stmt = (
        stmt.where(Document.id.notin_(done_here))
        .where(Document.id.notin_(exhausted))
        .where(Document.id.notin_(skipped))
        .order_by(Document.id)
        .limit(limit)
    )
    if require_consolidated:
        stmt = stmt.where(Document.consolidated_id.isnot(None))

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def stage_counts(session: AsyncSession) -> dict[str, dict[str, int]]:
    """Resumen del estado del pipeline: {etapa: {estado: n}}. Para el CLI/admin."""
    from sqlalchemy import func

    result = await session.execute(
        select(PipelineState.stage, PipelineState.status, func.count())
        .group_by(PipelineState.stage, PipelineState.status)
    )
    summary: dict[str, dict[str, int]] = {}
    for stage, status, count in result.all():
        summary.setdefault(stage.value, {})[status.value] = count
    return summary
