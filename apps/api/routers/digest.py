"""Endpoint del 'BOE del día': agrupado por categoría editorial, sin ruido.

El triaje (boe/enrich/triage.py) da a cada documento una categoría y una
relevancia 0-100. Aquí la portada se compone así:
  - highlights: top por relevancia (con resumen si lo hay)
  - categories: grupos de valor (ayudas, normas, oposiciones, otras) con sus
    mejores items ordenados por relevancia
  - noise: recuento colapsado de nombramientos/edictos/anuncios
  - groups (compat): la antigua agrupación por ámbito
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.core.db import get_session
from boe.core.enums import Scope
from boe.core.models import Document
from boe.core.schemas import (
    CategoryGroup,
    DigestGroup,
    DigestItem,
    DigestOut,
    NoiseSummary,
)
from boe.enrich.triage import CAT_OTRAS, CATEGORY_LABEL, NOISE_CATEGORIES

router = APIRouter()

_SCOPE_PRIORITY = {Scope.NACIONAL: 3, Scope.EUROPEO: 2, Scope.AUTONOMICO: 1, Scope.OTRO: 0}

# Orden editorial de los grupos de valor en portada.
_CATEGORY_ORDER = ["ayudas", "normas", "oposiciones", CAT_OTRAS]
# Máximo de items por grupo (el resto se ve en /buscar).
_PER_CATEGORY = 9


def _to_item(doc: Document) -> DigestItem:
    short = doc.summaries[0].short if doc.summaries else None
    return DigestItem(
        boe_id=doc.boe_id,
        title=doc.title,
        departamento=doc.departamento,
        scope=doc.scope,
        short=short,
        url_html=doc.url_html,
        category=doc.category,
        relevance=doc.relevance,
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

    # ─── Portada editorial: categorías de valor + ruido colapsado ───────────
    by_cat: dict[str, list[DigestItem]] = {}
    noise_breakdown: dict[str, int] = {}
    for item in items:
        cat = item.category or CAT_OTRAS
        if cat in NOISE_CATEGORIES:
            noise_breakdown[cat] = noise_breakdown.get(cat, 0) + 1
        else:
            by_cat.setdefault(cat, []).append(item)

    categories = []
    for cat in _CATEGORY_ORDER:
        cat_items = by_cat.pop(cat, [])
        if not cat_items:
            continue
        cat_items.sort(key=lambda it: (it.relevance or 0, it.short is not None), reverse=True)
        categories.append(
            CategoryGroup(
                category=cat,
                label=CATEGORY_LABEL.get(cat, cat),
                count=len(cat_items),
                items=cat_items[:_PER_CATEGORY],
            )
        )
    # Categorías no previstas en el orden (robustez): al final.
    for cat, cat_items in by_cat.items():
        cat_items.sort(key=lambda it: (it.relevance or 0), reverse=True)
        categories.append(
            CategoryGroup(
                category=cat,
                label=CATEGORY_LABEL.get(cat, cat),
                count=len(cat_items),
                items=cat_items[:_PER_CATEGORY],
            )
        )

    noise = NoiseSummary(
        total=sum(noise_breakdown.values()), breakdown=noise_breakdown
    ) if noise_breakdown else None

    # Destacados: máxima relevancia; con resumen primero a igualdad.
    highlights = sorted(
        (it for it in items if (it.category or CAT_OTRAS) not in NOISE_CATEGORIES),
        key=lambda it: (it.relevance or 0, it.short is not None),
        reverse=True,
    )[:5]
    # Si el triaje aún no ha corrido (todo sin relevancia), degrada al criterio antiguo.
    if not highlights:
        highlights = sorted(
            items,
            key=lambda it: (_SCOPE_PRIORITY.get(it.scope, 0), it.short is not None),
            reverse=True,
        )[:5]

    # ─── Compat: agrupación por ámbito ──────────────────────────────────────
    by_scope: dict[Scope, list[DigestItem]] = {}
    for item in items:
        by_scope.setdefault(item.scope, []).append(item)
    group_out = [
        DigestGroup(scope=scope, count=len(its), items=its)
        for scope, its in sorted(
            by_scope.items(), key=lambda kv: _SCOPE_PRIORITY.get(kv[0], 0), reverse=True
        )
    ]

    return DigestOut(
        fecha=fecha,
        total=len(items),
        highlights=highlights,
        groups=group_out,
        categories=categories,
        noise=noise,
    )
