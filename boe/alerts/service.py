"""Servicio de alertas: casa documentos, envía y registra la entrega.

Idempotente: cada (suscripción, documento) se registra en `notifications`, así
que reejecutar no reenvía. El registro se crea aunque el envío falle (con estado
FAILED), pero solo bloquea reenvíos si fue SENT.
"""

from __future__ import annotations

from datetime import date

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from boe.alerts.matcher import find_matches
from boe.alerts.notifiers import get_notifier
from boe.core.db import SessionLocal
from boe.core.enums import NotificationStatus
from boe.core.models import Document, Notification, Subscription

log = structlog.get_logger(__name__)


def _render(sub: Subscription, docs: list[Document]) -> tuple[str, str]:
    subject = f"AlertaBOE · {len(docs)} novedad(es) que te afectan"
    lines = ["Estas publicaciones del BOE coinciden con tu alerta:\n"]
    for d in docs:
        short = d.summaries[0].short if d.summaries else None
        lines.append(f"• {d.title}")
        if short:
            lines.append(f"  {short}")
        lines.append(f"  https://boe.es/diario_boe/txt.php?id={d.boe_id}\n")
    lines.append("\nInformación divulgativa, no asesoramiento legal.")
    return subject, "\n".join(lines)


async def run_for_date(
    fecha: date,
    *,
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
) -> dict[str, int]:
    """Envía alertas de un día. Devuelve {enviadas, fallidas, suscripciones}."""
    sent = failed = 0
    async with session_factory() as session:
        matches = await find_matches(session, fecha)
        for match in matches:
            # Carga resúmenes de los documentos para el cuerpo.
            doc_ids = [d.id for d in match.documents]
            docs = (
                await session.execute(
                    select(Document).where(Document.id.in_(doc_ids))
                )
            ).scalars().all()
            # selectinload de summaries de forma perezosa segura:
            for d in docs:
                await session.refresh(d, attribute_names=["summaries"])

            sub = match.subscription
            subject, body = _render(sub, docs)
            notifier = get_notifier(sub.channel)
            result = await notifier.send(
                destination=sub.destination, subject=subject, body=body
            )

            status = NotificationStatus.SENT if result.ok else NotificationStatus.FAILED
            for d in match.documents:
                session.add(
                    Notification(
                        subscription_id=sub.id,
                        document_id=d.id,
                        channel=sub.channel,
                        status=status,
                        error=result.error,
                    )
                )
            if result.ok:
                sent += 1
            else:
                failed += 1

        await session.commit()

    log.info("alerts_run", fecha=str(fecha), enviadas=sent, fallidas=failed)
    return {"enviadas": sent, "fallidas": failed, "suscripciones": len(matches)}
