"""Búsqueda híbrida: full-text (español) + vectorial (pgvector), fusionadas.

Combina dos señales complementarias:
  - **full-text** sobre `documents.search_vector` con `websearch_to_tsquery`
    (maneja consultas naturales, comillas, OR), ranqueado con `ts_rank`.
  - **vectorial**: distancia coseno del embedding de la consulta al de cada
    documento (índice HNSW). Solo se usa si hay modelo de embeddings disponible.

Se combinan con Reciprocal Rank Fusion (RRF), robusto y sin necesidad de
normalizar escalas dispares. Si no hay embeddings (consulta o corpus sin
vector), degrada a full-text puro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.core.enums import Scope
from boe.core.models import Document, Embedding, Region, Topic

_RRF_K = 60


@dataclass
class SearchFilters:
    fecha: date | None = None
    desde: date | None = None
    hasta: date | None = None
    scope: Scope | None = None
    topic: str | None = None          # slug del tema
    region: str | None = None         # nombre de la CCAA
    departamento: str | None = None


@dataclass
class SearchHit:
    document: Document
    score: float
    matched: list[str] = field(default_factory=list)  # señales que lo trajeron


def _apply_filters(stmt: Select, filters: SearchFilters) -> Select:
    if filters.fecha:
        stmt = stmt.where(Document.published_at == filters.fecha)
    if filters.desde:
        stmt = stmt.where(Document.published_at >= filters.desde)
    if filters.hasta:
        stmt = stmt.where(Document.published_at <= filters.hasta)
    if filters.scope:
        stmt = stmt.where(Document.scope == filters.scope)
    if filters.departamento:
        stmt = stmt.where(Document.departamento.ilike(f"%{filters.departamento}%"))
    if filters.topic:
        stmt = stmt.where(Document.topics.any(Topic.slug == filters.topic))
    if filters.region:
        stmt = stmt.where(Document.regions.any(Region.name == filters.region))
    return stmt


async def _fulltext_ids(
    session: AsyncSession, query: str, filters: SearchFilters, limit: int
) -> list[int]:
    tsquery = func.websearch_to_tsquery("spanish", query)
    rank = func.ts_rank(Document.search_vector, tsquery)
    stmt = (
        select(Document.id)
        .where(Document.search_vector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(limit)
    )
    stmt = _apply_filters(stmt, filters)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _vector_ids(
    session: AsyncSession, query_vector: list[float], filters: SearchFilters, limit: int
) -> list[int]:
    distance = Embedding.vector.cosine_distance(query_vector)
    stmt = (
        select(Document.id)
        .join(Embedding, Embedding.document_id == Document.id)
        .order_by(distance.asc())
        .limit(limit)
    )
    stmt = _apply_filters(stmt, filters)
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _rrf(rankings: dict[str, list[int]]) -> dict[int, tuple[float, list[str]]]:
    """Reciprocal Rank Fusion. Devuelve {doc_id: (score, señales)}."""
    fused: dict[int, tuple[float, list[str]]] = {}
    for signal, ids in rankings.items():
        for rank, doc_id in enumerate(ids):
            score, matched = fused.get(doc_id, (0.0, []))
            fused[doc_id] = (score + 1.0 / (_RRF_K + rank + 1), [*matched, signal])
    return fused


def _embed_query(query: str) -> list[float] | None:
    """Embebe la consulta si hay modelo disponible; None si no."""
    try:
        from boe.search.embeddings import embed_text
    except ImportError:
        return None
    try:
        return embed_text(query)
    except Exception:  # noqa: BLE001 — el modelo puede no cargar; degradamos a full-text
        return None


async def search(
    session: AsyncSession,
    query: str,
    *,
    filters: SearchFilters | None = None,
    limit: int = 20,
    use_vector: bool = True,
) -> list[SearchHit]:
    """Búsqueda híbrida ordenada por relevancia."""
    filters = filters or SearchFilters()
    pool = max(limit * 3, 30)

    rankings: dict[str, list[int]] = {}
    if query.strip():
        rankings["texto"] = await _fulltext_ids(session, query, filters, pool)
        if use_vector:
            query_vector = _embed_query(query)
            if query_vector is not None:
                rankings["vector"] = await _vector_ids(
                    session, query_vector, filters, pool
                )

    # Sin consulta textual → listado filtrado por fecha reciente.
    if not rankings:
        stmt = _apply_filters(select(Document.id), filters).order_by(
            Document.published_at.desc(), Document.id.desc()
        ).limit(limit)
        rankings["reciente"] = list((await session.execute(stmt)).scalars().all())

    fused = _rrf(rankings)
    top = sorted(fused.items(), key=lambda kv: kv[1][0], reverse=True)[:limit]
    if not top:
        return []

    ids = [doc_id for doc_id, _ in top]
    docs = (
        await session.execute(
            select(Document)
            .where(Document.id.in_(ids))
            .options(selectinload(Document.topics), selectinload(Document.regions))
        )
    ).scalars().all()
    by_id = {d.id: d for d in docs}

    return [
        SearchHit(document=by_id[doc_id], score=score, matched=matched)
        for doc_id, (score, matched) in top
        if doc_id in by_id
    ]
