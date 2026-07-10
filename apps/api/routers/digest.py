"""Endpoint del 'BOE del día': agrupado, resumido y con destacados."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.core.db import get_session
from boe.core.enums import Scope
from boe.core.models import Document
from boe.core.schemas import DigestGroup, DigestItem, DigestOut

router = APIRouter()

# Prioridad de ámbito para elegir destacados (mayor primero).
_SCOPE_PRIORITY = {Scope.NACIONAL: 3, Scope.EUROPEO: 2, Scope.AUTONOMICO: 1, Scope.OTRO: 0}


def _to_item(doc: Document) -> DigestItem:
    short = doc.summaries[0].short if doc.summaries else None
    return DigestItem(
        boe_id=doc.boe_id,
        title=doc.title,
        departamento=doc.departamento,
        scope=doc.scope,
        short=short,
        url_html=doc.url_html,
    )


@router.get("/digest/{fecha}", response_model=DigestOut)
async def digest(fecha: date, session: AsyncSession = Depends(get_session)) -> DigestOut:
    docs = (
        await session.execute(
            select(Document)
            .where(Document.published_at == fecha)
            .options(selectinload(Document.summaries))
            .order_by(Document.id)
        )
    ).scalars().all()

    items = [_to_item(d) for d in docs]

    # Agrupación por ámbito.
    groups: dict[Scope, list[DigestItem]] = {}
    for item in items:
        groups.setdefault(item.scope, []).append(item)

    group_out = [
        DigestGroup(scope=scope, count=len(its), items=its)
        for scope, its in sorted(
            groups.items(), key=lambda kv: _SCOPE_PRIORITY.get(kv[0], 0), reverse=True
        )
    ]

    # Destacados: los de mayor ámbito que ya tienen resumen breve, luego el resto.
    highlights = sorted(
        items,
        key=lambda it: (_SCOPE_PRIORITY.get(it.scope, 0), it.short is not None),
        reverse=True,
    )[:5]

    return DigestOut(
        fecha=fecha, total=len(items), highlights=highlights, groups=group_out
    )
