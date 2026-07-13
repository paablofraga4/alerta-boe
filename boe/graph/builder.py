"""Construcción del grafo normativo: referencias de una norma consolidada.

Toma las aristas parseadas del bloque `analisis` (`ReferenceEntry`) y las
persiste como filas `Reference`, resolviendo el destino a un documento local si
ya está ingerido. Idempotente gracias al UniqueConstraint de la tabla.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from boe.clients.dto import ReferenceEntry
from boe.core.models import Document, Reference


async def _resolve_target_id(session: AsyncSession, boe_id: str | None) -> int | None:
    if not boe_id:
        return None
    result = await session.execute(
        select(Document.id).where(Document.boe_id == boe_id)
    )
    return result.scalar_one_or_none()


async def store_references(
    session: AsyncSession, source_id: int, entries: list[ReferenceEntry]
) -> int:
    """Inserta las referencias de un documento. Devuelve cuántas nuevas se crearon."""
    inserted = 0
    for entry in entries:
        target_id = await _resolve_target_id(session, entry.target_boe_id)
        stmt = (
            insert(Reference)
            .values(
                source_id=source_id,
                target_id=target_id,
                target_boe_id=entry.target_boe_id,
                target_title=entry.target_title,
                rel_type=entry.rel_type,
                direction=entry.direction,
                raw_text=entry.raw_text,
            )
            .on_conflict_do_nothing(constraint="uq_reference")
        )
        result = await session.execute(stmt)
        inserted += result.rowcount or 0
    await session.flush()
    return inserted
