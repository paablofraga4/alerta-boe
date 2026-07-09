"""Endpoints de salud/diagnóstico."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from boe import __version__
from boe.core.db import get_session

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_session)) -> dict:
    """Comprueba conectividad con Postgres."""
    await session.execute(text("SELECT 1"))
    return {"database": "ok"}
