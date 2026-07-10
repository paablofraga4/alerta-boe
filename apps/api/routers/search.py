"""Endpoint de búsqueda híbrida."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from boe.core.db import get_session
from boe.core.schemas import DocumentOut, SearchHitOut, SearchRequest, SearchResponse
from boe.search.hybrid import SearchFilters, search

router = APIRouter()


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
