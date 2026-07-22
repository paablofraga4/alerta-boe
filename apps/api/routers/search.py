"""Endpoint de búsqueda híbrida."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from boe.core.db import get_session
from boe.core.models import Topic, document_topics
from boe.core.schemas import (
    DocumentOut,
    SearchHitOut,
    SearchRequest,
    SearchResponse,
    TopicCountOut,
    TopicListResponse,
)
from boe.search.hybrid import SearchFilters, search

router = APIRouter()


@router.get("/topics", response_model=TopicListResponse)
async def list_topics(session: AsyncSession = Depends(get_session)) -> TopicListResponse:
    """Temas con recuento de publicaciones, ordenados por volumen."""
    n_docs = func.count(document_topics.c.document_id)
    stmt = (
        select(Topic.name, Topic.slug, n_docs)
        .join(document_topics, document_topics.c.topic_id == Topic.id, isouter=True)
        .group_by(Topic.id)
        .order_by(n_docs.desc(), Topic.name)
    )
    rows = (await session.execute(stmt)).all()
    return TopicListResponse(
        topics=[TopicCountOut(name=n, slug=s, count=c) for n, s, c in rows]
    )


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    body: SearchRequest, session: AsyncSession = Depends(get_session)
) -> SearchResponse:
    filters = SearchFilters(
        fecha=body.fecha,
        desde=body.desde,
        hasta=body.hasta,
        scope=body.scope,
        topic=body.topic,
        region=body.region,
        departamento=body.departamento,
        category=body.category,
    )
    hits = await search(session, body.query, filters=filters, limit=body.limit)
    return SearchResponse(
        query=body.query,
        total=len(hits),
        results=[
            SearchHitOut(
                document=DocumentOut.model_validate(h.document),
                score=round(h.score, 5),
                matched=h.matched,
            )
            for h in hits
        ],
    )
