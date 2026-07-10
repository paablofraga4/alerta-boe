"""Chat RAG con citas obligatorias sobre las publicaciones del BOE."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from boe.core.config import settings
from boe.core.db import get_session
from boe.core.schemas import ChatRequest, ChatResponse, Citation
from boe.llm.prompts import rag_messages
from boe.llm.router import LLMError, get_router
from boe.search.hybrid import SearchFilters, search

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, session: AsyncSession = Depends(get_session)
) -> ChatResponse:
    llm = get_router()
    if not llm.has_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No hay proveedor LLM configurado para el chat.",
        )

    top_k = body.top_k or settings.chat_top_k
    filters = SearchFilters(fecha=body.fecha, scope=body.scope)
    hits = await search(session, body.message, filters=filters, limit=top_k)

    if not hits:
        return ChatResponse(
            answer="No he encontrado publicaciones del BOE relacionadas con tu consulta.",
            citations=[],
        )

    contexts = [
        (h.document.boe_id, h.document.title, h.document.full_text or h.document.title)
        for h in hits
    ]
    try:
        answer = await llm.complete(rag_messages(body.message, contexts), temperature=0.3)
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    citations = [
        Citation(boe_id=h.document.boe_id, title=h.document.title, url_html=h.document.url_html)
        for h in hits
    ]
    return ChatResponse(answer=answer, citations=citations)
