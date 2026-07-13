"""Cola de la fábrica de contenido: revisión y publicación humana-en-el-bucle."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boe.content.publishers import get_publisher
from boe.core.db import get_session
from boe.core.enums import ContentChannel, ContentStatus
from boe.core.models import ContentPost
from boe.core.schemas import ContentListResponse, ContentPostOut

router = APIRouter()


def _to_out(post: ContentPost) -> ContentPostOut:
    out = ContentPostOut.model_validate(post)
    out.boe_id = post.document.boe_id if post.document else None
    return out


async def _get(session: AsyncSession, post_id: int) -> ContentPost:
    post = (
        await session.execute(
            select(ContentPost)
            .where(ContentPost.id == post_id)
            .options(selectinload(ContentPost.document))
        )
    ).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Pieza de contenido no encontrada")
    return post


@router.get("/content", response_model=ContentListResponse)
async def list_content(
    session: AsyncSession = Depends(get_session),
    status: ContentStatus | None = None,
    channel: ContentChannel | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> ContentListResponse:
    stmt = (
        select(ContentPost)
        .options(selectinload(ContentPost.document))
        .order_by(ContentPost.interest_score.desc().nullslast(), ContentPost.id.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(ContentPost.status == status)
    if channel:
        stmt = stmt.where(ContentPost.channel == channel)
    posts = (await session.execute(stmt)).scalars().all()
    return ContentListResponse(total=len(posts), posts=[_to_out(p) for p in posts])


@router.post("/content/{post_id}/approve", response_model=ContentPostOut)
async def approve(post_id: int, session: AsyncSession = Depends(get_session)) -> ContentPostOut:
    post = await _get(session, post_id)
    post.status = ContentStatus.APPROVED
    await session.commit()
    return _to_out(post)


@router.post("/content/{post_id}/reject", response_model=ContentPostOut)
async def reject(post_id: int, session: AsyncSession = Depends(get_session)) -> ContentPostOut:
    post = await _get(session, post_id)
    post.status = ContentStatus.REJECTED
    await session.commit()
    return _to_out(post)


@router.post("/content/{post_id}/publish", response_model=ContentPostOut)
async def publish(post_id: int, session: AsyncSession = Depends(get_session)) -> ContentPostOut:
    """Publica una pieza aprobada (modo dry-run hasta que haya credenciales)."""
    post = await _get(session, post_id)
    if post.status != ContentStatus.APPROVED:
        raise HTTPException(
            status_code=409, detail="Solo se pueden publicar piezas aprobadas."
        )
    publisher = get_publisher(post.channel)
    result = await publisher.publish(text=post.script or "", asset_path=post.asset_path)
    if not result.ok:
        post.status = ContentStatus.FAILED
        await session.commit()
        raise HTTPException(status_code=502, detail=result.error or "Fallo al publicar")

    post.status = ContentStatus.PUBLISHED
    post.external_id = result.external_id
    post.published_at = datetime.now(UTC)
    await session.commit()
    return _to_out(post)
