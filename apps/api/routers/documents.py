"""Endpoints de documentos y del hilo normativo.

En F0 se entregan los básicos leyendo del ORM. La búsqueda híbrida (F2) y la
visualización del grafo (F4) se construirán sobre estos cimientos.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.core.db import get_session
from boe.core.enums import ReferenceDirection
from boe.core.models import Document, Reference
from boe.core.schemas import (
    DocumentDetailOut,
    DocumentOut,
    ReferenceOut,
    ThreadOut,
)

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    session: AsyncSession = Depends(get_session),
    fecha: date | None = Query(None, description="Filtra por fecha de publicación"),
    departamento: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[Document]:
    stmt = (
        select(Document)
        .options(selectinload(Document.topics), selectinload(Document.regions))
        .order_by(Document.published_at.desc(), Document.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if fecha:
        stmt = stmt.where(Document.published_at == fecha)
    if departamento:
        stmt = stmt.where(Document.departamento.ilike(f"%{departamento}%"))

    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/documents/{boe_id}", response_model=DocumentDetailOut)
async def get_document(
    boe_id: str, session: AsyncSession = Depends(get_session)
) -> Document:
    stmt = (
        select(Document)
        .where(Document.boe_id == boe_id)
        .options(
            selectinload(Document.topics),
            selectinload(Document.regions),
            selectinload(Document.summaries),
        )
    )
    doc = (await session.execute(stmt)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.get("/documents/{boe_id}/thread", response_model=ThreadOut)
async def get_thread(
    boe_id: str, session: AsyncSession = Depends(get_session)
) -> ThreadOut:
    """El hilo de una publicación: sus precedentes y sus derivadas."""
    doc = (
        await session.execute(select(Document).where(Document.boe_id == boe_id))
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    refs = (
        await session.execute(select(Reference).where(Reference.source_id == doc.id))
    ).scalars().all()

    anteriores = [
        ReferenceOut.model_validate(r)
        for r in refs
        if r.direction == ReferenceDirection.ANTERIOR
    ]
    posteriores = [
        ReferenceOut.model_validate(r)
        for r in refs
        if r.direction == ReferenceDirection.POSTERIOR
    ]
    return ThreadOut(
        boe_id=doc.boe_id,
        title=doc.title,
        anteriores=anteriores,
        posteriores=posteriores,
    )
