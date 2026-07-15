"""«El BOE en 3 minutos»: digest semanal por suscripción.

Para cada suscripción activa, junta lo publicado en los últimos 7 días que casa
con sus filtros (mismo criterio AND que las alertas diarias) y los plazos que
siguen abiertos, y lo envía por su canal (email/Telegram). Es stateless: no
registra en `notifications` (eso es de las alertas por documento); el cron
semanal es quien decide cuándo se envía.
"""

from __future__ import annotations

from datetime import date, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from boe.alerts.matcher import _matches
from boe.alerts.notifiers import get_notifier
from boe.core.config import settings
from boe.core.db import SessionLocal
from boe.core.models import Document, Subscription
from boe.enrich.plazos import parse_fecha_es

log = structlog.get_logger(__name__)

_TOP_N = 5
_WEB_BASE = settings.web_base_url.rstrip("/")


def _fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def render_digest(
    docs: list[Document], *, desde: date, hasta: date
) -> tuple[str, str] | None:
    """Compone (asunto, cuerpo) del digest. None si no hay nada que contar."""
    if not docs:
        return None

    # Con resumen primero, más recientes primero.
    docs = sorted(
        docs, key=lambda d: (not d.summaries, d.published_at), reverse=False
    )
    docs_top = sorted(docs, key=lambda d: d.published_at, reverse=True)[:_TOP_N]

    subject = f"El BOE en 3 minutos · semana del {_fmt(desde)} al {_fmt(hasta)}"
    lines = [
        f"Lo esencial del BOE de tu semana ({len(docs)} publicaciones que te afectan):",
        "",
    ]
    for i, d in enumerate(docs_top, start=1):
        short = d.summaries[0].short if d.summaries else None
        lines.append(f"{i}. {short or d.title}")
        if short:
            lines.append(f"   {d.title}")
        lines.append(f"   {_WEB_BASE}/documento/{d.boe_id}")
        lines.append("")

    # Plazos aún abiertos de TODO lo casado (no solo del top).
    plazos: list[tuple[date, str, str]] = []
    for d in docs:
        for s in d.summaries:
            for plazo in (s.structured or {}).get("plazos", []):
                fecha = parse_fecha_es(
                    str(plazo.get("fecha", "")), referencia=d.published_at
                )
                accion = str(plazo.get("accion", "")).strip()
                if fecha and fecha >= hasta and accion:
                    plazos.append((fecha, accion, d.boe_id))
    if plazos:
        plazos.sort()
        lines.append("⏳ Plazos que siguen abiertos:")
        for fecha, accion, boe_id in plazos[:8]:
            lines.append(f"• {_fmt(fecha)} — {accion} ({_WEB_BASE}/documento/{boe_id})")
        lines.append("")

    lines.append(f"Radar de plazos completo: {_WEB_BASE}/radar")
    lines.append("")
    lines.append("Información divulgativa, no asesoramiento legal.")
    return subject, "\n".join(lines)


async def run_weekly(
    hasta: date | None = None,
    *,
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
) -> dict[str, int]:
    """Envía el digest semanal a cada suscripción activa con novedades."""
    hasta = hasta or date.today()
    desde = hasta - timedelta(days=6)

    sent = failed = skipped = 0
    async with session_factory() as session:
        subs = (
            await session.execute(
                select(Subscription).where(Subscription.active.is_(True))
            )
        ).scalars().all()
        docs = (
            await session.execute(
                select(Document)
                .where(Document.published_at >= desde, Document.published_at <= hasta)
                .options(
                    selectinload(Document.topics),
                    selectinload(Document.regions),
                    selectinload(Document.summaries),
                )
            )
        ).scalars().all()

        for sub in subs:
            matched = [d for d in docs if _matches(d, sub)]
            rendered = render_digest(matched, desde=desde, hasta=hasta)
            if rendered is None:
                skipped += 1
                continue
            subject, body = rendered
            result = await get_notifier(sub.channel).send(
                destination=sub.destination, subject=subject, body=body
            )
            if result.ok:
                sent += 1
            else:
                failed += 1
                log.warning("digest_failed", destination=sub.destination, error=result.error)

    log.info("digest_weekly", hasta=str(hasta), enviados=sent, fallidos=failed, sin_novedades=skipped)
    return {"enviados": sent, "fallidos": failed, "sin_novedades": skipped}
