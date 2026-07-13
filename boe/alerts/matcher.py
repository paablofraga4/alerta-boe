"""Cruce de documentos con suscripciones (F6).

Para una fecha, encuentra qué documentos casan con cada suscripción activa y que
no se han notificado aún. Un documento casa si cumple TODOS los filtros definidos
de la suscripción (tema, región, ámbito, palabra clave) — combinados en AND.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.core.models import Document, Notification, Subscription


@dataclass
class Match:
    subscription: Subscription
    documents: list[Document]


def _matches(doc: Document, sub: Subscription) -> bool:
    if sub.topic_slug and not any(t.slug == sub.topic_slug for t in doc.topics):
        return False
    if sub.region_name and not any(r.name == sub.region_name for r in doc.regions):
        return False
    if sub.scope and doc.scope != sub.scope:
        return False
    if sub.keyword:
        haystack = f"{doc.title} {doc.full_text or ''}".lower()
        if sub.keyword.lower() not in haystack:
            return False
    return True


async def find_matches(session: AsyncSession, fecha: date) -> list[Match]:
    """Suscripciones activas con los documentos del día que les casan y aún no
    se les han notificado."""
    subs = (
        await session.execute(select(Subscription).where(Subscription.active.is_(True)))
    ).scalars().all()
    if not subs:
        return []

    docs = (
        await session.execute(
            select(Document)
            .where(Document.published_at == fecha)
            .options(selectinload(Document.topics), selectinload(Document.regions))
        )
    ).scalars().all()

    # Documentos ya notificados por suscripción (para no repetir).
    already = (
        await session.execute(
            select(Notification.subscription_id, Notification.document_id)
        )
    ).all()
    sent: set[tuple[int, int]] = {(s, d) for s, d in already}

    results: list[Match] = []
    for sub in subs:
        hits = [
            d for d in docs
            if _matches(d, sub) and (sub.id, d.id) not in sent
        ]
        if hits:
            results.append(Match(subscription=sub, documents=hits))
    return results
