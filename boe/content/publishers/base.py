"""Interfaz de publicadores por canal.

La publicación real en LinkedIn/X/TikTok requiere credenciales y (en TikTok)
aprobación de app. Se define aquí la interfaz y un `DryRunPublisher` que simula
la publicación —útil para el flujo humano-en-el-bucle y los tests— mientras las
integraciones reales se activan por configuración.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from boe.core.enums import ContentChannel


@dataclass
class PublishResult:
    ok: bool
    external_id: str | None = None
    error: str | None = None


class Publisher(Protocol):
    channel: ContentChannel

    async def publish(self, *, text: str, asset_path: str | None = None) -> PublishResult:
        ...


class DryRunPublisher:
    """Simula la publicación: no llama a ninguna API externa."""

    def __init__(self, channel: ContentChannel) -> None:
        self.channel = channel

    async def publish(self, *, text: str, asset_path: str | None = None) -> PublishResult:
        return PublishResult(ok=True, external_id=f"dryrun-{self.channel.value}")


def get_publisher(channel: ContentChannel) -> Publisher:
    """Devuelve el publicador del canal.

    Por ahora siempre en modo dry-run. Cuando existan credenciales, aquí se
    seleccionará el publicador real (linkedin.py, x.py, tiktok.py).
    """
    return DryRunPublisher(channel)
