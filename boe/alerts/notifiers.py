"""Notificadores por canal: email (SMTP) y Telegram (Bot API).

Ambos degradan a dry-run si falta configuración, para que el flujo de alertas
funcione en desarrollo/tests sin credenciales.
"""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage

import httpx
import structlog

from boe.core.config import settings
from boe.core.enums import NotificationChannel

log = structlog.get_logger(__name__)


@dataclass
class DeliveryResult:
    ok: bool
    dry_run: bool = False
    error: str | None = None


class EmailNotifier:
    channel = NotificationChannel.EMAIL

    async def send(self, *, destination: str, subject: str, body: str) -> DeliveryResult:
        if not settings.smtp_host:
            log.info("email_dry_run", to=destination, subject=subject)
            return DeliveryResult(ok=True, dry_run=True)
        try:
            import aiosmtplib  # import perezoso: extra opcional
        except ImportError:  # pragma: no cover
            return DeliveryResult(ok=False, error="aiosmtplib no instalado")

        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = destination
        message["Subject"] = subject
        message.set_content(body)
        try:  # pragma: no cover - requiere SMTP real
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
            return DeliveryResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(ok=False, error=str(exc))


class TelegramNotifier:
    channel = NotificationChannel.TELEGRAM

    async def send(self, *, destination: str, subject: str, body: str) -> DeliveryResult:
        token = settings.telegram_bot_token
        text = f"*{subject}*\n\n{body}"
        if not token:
            log.info("telegram_dry_run", chat=destination)
            return DeliveryResult(ok=True, dry_run=True)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:  # pragma: no cover - requiere Telegram real
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    json={"chat_id": destination, "text": text, "parse_mode": "Markdown"},
                )
                resp.raise_for_status()
            return DeliveryResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(ok=False, error=str(exc))


def get_notifier(channel: NotificationChannel):
    return EmailNotifier() if channel == NotificationChannel.EMAIL else TelegramNotifier()
