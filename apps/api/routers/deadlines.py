"""Radar de plazos: agrega los plazos vivos extraídos por el agente.

Recorre los briefs estructurados (`summaries.structured.plazos`), convierte las
fechas en texto a fechas reales (`parse_fecha_es`) y devuelve solo los plazos
que aún no han vencido, ordenados por urgencia. El BOE como lista de cosas que
puedes perder si no actúas.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.core.db import get_session
from boe.core.enums import Scope
from boe.core.models import Document, Summary, Topic
from boe.core.schemas import DeadlineListResponse, DeadlineOut, TopicOut
from boe.enrich.plazos import parse_fecha_es

router = APIRouter()


@router.get("/deadlines", response_model=DeadlineListResponse)
async def list_deadlines(
    topic: str | None = Query(default=None, description="Slug de tema"),
    scope: Scope | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
) -> DeadlineListResponse:
    hoy = date.today()

    stmt = (
        select(Summary, Document)
        .join(Document, Document.id == Summary.document_id)
        .where(Summary.structured.isnot(None))
        .options(selectinload(Document.topics))
        .order_by(Document.published_at.desc())
    )
    if scope:
        stmt = stmt.where(Document.scope == scope)
    if topic:
        stmt = stmt.where(Document.topics.any(Topic.slug == topic))

    rows = (await session.execute(stmt)).all()

    deadlines: list[DeadlineOut] = []
    for summary, doc in rows:
        for plazo in (summary.structured or {}).get("plazos", []):
            fecha_texto = str(plazo.get("fecha", ""))
            accion = str(plazo.get("accion", "")).strip()
            fecha = parse_fecha_es(fecha_texto, referencia=doc.published_at)
            if fecha is None or fecha < hoy or not accion:
                continue
            deadlines.append(
                DeadlineOut(
                    fecha=fecha,
                    fecha_texto=fecha_texto,
                    accion=accion,
                    dias_restantes=(fecha - hoy).days,
                    boe_id=doc.boe_id,
                    title=doc.title,
                    scope=doc.scope,
                    topics=[TopicOut.model_validate(t) for t in doc.topics],
                )
            )

    deadlines.sort(key=lambda d: (d.fecha, d.boe_id))
    return DeadlineListResponse(total=len(deadlines), deadlines=deadlines[:limit])
