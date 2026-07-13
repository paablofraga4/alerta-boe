"""Guionista: genera la pieza de contenido adaptada a cada canal."""

from __future__ import annotations

from boe.content.prompts import (
    LinkedInPost,
    TikTokScript,
    XThread,
    linkedin_messages,
    tiktok_messages,
    x_messages,
)
from boe.core.enums import ContentChannel
from boe.llm.router import LLMRouter


def tiktok_to_text(script: TikTokScript) -> str:
    """Aplana el guion de TikTok a texto legible (para almacenarlo/aprobarlo)."""
    puntos = "\n".join(f"• {p}" for p in script.points)
    return f"🎬 {script.hook}\n\n{puntos}\n\n👉 {script.cta}\n\n---\n{script.narration}"


async def write(
    router: LLMRouter,
    channel: ContentChannel,
    *,
    titulo: str,
    resumen: str,
    boe_id: str,
) -> tuple[str, dict]:
    """Genera la pieza. Devuelve (texto, extra) donde extra guarda la estructura
    original (útil para el render de vídeo o para publicar hilos de X)."""
    if channel == ContentChannel.LINKEDIN:
        post = await router.complete_structured(
            linkedin_messages(titulo, resumen, boe_id), LinkedInPost
        )
        return post.text, {}

    if channel == ContentChannel.X:
        thread = await router.complete_structured(
            x_messages(titulo, resumen, boe_id), XThread
        )
        return "\n\n---\n\n".join(thread.tweets), {"tweets": thread.tweets}

    if channel == ContentChannel.TIKTOK:
        script = await router.complete_structured(
            tiktok_messages(titulo, resumen, boe_id), TikTokScript
        )
        return tiktok_to_text(script), {
            "hook": script.hook,
            "points": script.points,
            "cta": script.cta,
            "narration": script.narration,
        }

    raise ValueError(f"Canal no soportado: {channel}")
