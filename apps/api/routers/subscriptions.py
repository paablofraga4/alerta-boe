"""Suscripciones a alertas del BOE por tema/región/ámbito/palabra clave (F6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from boe.core.db import get_session
from boe.core.enums import NotificationChannel
from boe.core.models import Subscription, User
from boe.core.schemas import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionOut,
)

router = APIRouter()


async def _get_or_create_user(session: AsyncSession, email: str) -> User:
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None:
        user = User(email=email)
        session.add(user)
        await session.flush()
    return user


@router.post("/subscriptions", response_model=SubscriptionOut, status_code=201)
async def create_subscription(
    body: SubscriptionCreate, session: AsyncSession = Depends(get_session)
) -> Subscription:
    if not any([body.topic_slug, body.region_name, body.scope, body.keyword]):
        raise HTTPException(
            status_code=422,
            detail="Define al menos un filtro (tema, región, ámbito o palabra clave).",
        )

    destination = body.destination
    if not destination:
        if body.channel == NotificationChannel.EMAIL:
            destination = body.email
        else:
            raise HTTPException(
                status_code=422,
                detail="Para Telegram indica 'destination' (chat_id).",
            )

    user = await _get_or_create_user(session, body.email)
    sub = Subscription(
        user_id=user.id,
        channel=body.channel,
        destination=destination,
        topic_slug=body.topic_slug,
        region_name=body.region_name,
        scope=body.scope,
        keyword=body.keyword,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


@router.get("/subscriptions", response_model=SubscriptionListResponse)
async def list_subscriptions(
    email: str = Query(..., description="Email del usuario"),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionListResponse:
    subs = (
        await session.execute(
            select(Subscription)
            .join(User, User.id == Subscription.user_id)
            .where(User.email == email)
            .order_by(Subscription.id)
        )
    ).scalars().all()
    return SubscriptionListResponse(
        total=len(subs), subscriptions=[SubscriptionOut.model_validate(s) for s in subs]
    )


@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    sub = await session.get(Subscription, subscription_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    await session.delete(sub)
    await session.commit()
