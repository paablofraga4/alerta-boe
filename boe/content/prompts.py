"""Prompts y salidas estructuradas de la fábrica de contenido.

Un guionista por canal (LinkedIn, X, TikTok) y un validador anti-alucinación.
Todo el contenido debe apoyarse en el resumen/título reales de la publicación y
citar su boe_id, para no inventar en un dominio legal.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from boe.core.enums import ContentChannel
from boe.llm.router import Message

CONTENT_PROMPT_VERSION = "v1"

_DISCLAIMER = "Esto es información divulgativa, no asesoramiento legal."


class LinkedInPost(BaseModel):
    text: str = Field(description="Post de 800-1200 caracteres, tono profesional.")


class XThread(BaseModel):
    tweets: list[str] = Field(description="3-5 tuits de ≤280 caracteres cada uno.")


class TikTokScript(BaseModel):
    hook: str = Field(description="Gancho de ≤3 segundos que pare el scroll.")
    points: list[str] = Field(description="3 puntos claros y concretos.")
    cta: str = Field(description="Llamada a la acción final.")
    narration: str = Field(description="Texto corrido para locución TTS (45-60 s).")


def _base_context(titulo: str, resumen: str, boe_id: str) -> str:
    return (
        f"Publicación del BOE (id {boe_id}).\n"
        f"Título: {titulo}\n"
        f"Resumen: {resumen}\n\n"
        "Basa TODO el contenido en esta información. No inventes cifras, fechas "
        "ni normas. No des asesoramiento legal vinculante."
    )


def linkedin_messages(titulo: str, resumen: str, boe_id: str) -> list[Message]:
    return [
        {"role": "system", "content": "Eres community manager especializado en divulgación legal clara."},
        {
            "role": "user",
            "content": (
                f"{_base_context(titulo, resumen, boe_id)}\n\n"
                "Escribe un post de LinkedIn (800-1200 caracteres): gancho inicial, "
                "3 claves de por qué importa y a quién afecta, y cierre. Tono "
                f"profesional y cercano. Incluye el disclaimer: '{_DISCLAIMER}'. "
                f"Menciona la fuente [{boe_id}]. Devuelve JSON {{\"text\": ...}}."
            ),
        },
    ]


def x_messages(titulo: str, resumen: str, boe_id: str) -> list[Message]:
    return [
        {"role": "system", "content": "Redactas hilos de X claros y directos sobre el BOE."},
        {
            "role": "user",
            "content": (
                f"{_base_context(titulo, resumen, boe_id)}\n\n"
                "Escribe un hilo de 3-5 tuits (cada uno ≤280 caracteres). El primero "
                "es el gancho. El último cita la fuente [" + boe_id + "] e incluye "
                f"el disclaimer: '{_DISCLAIMER}'. Devuelve JSON {{\"tweets\": [...]}}."
            ),
        },
    ]


def tiktok_messages(titulo: str, resumen: str, boe_id: str) -> list[Message]:
    return [
        {"role": "system", "content": "Escribes guiones de vídeo corto (TikTok/Reels) sobre normativa."},
        {
            "role": "user",
            "content": (
                f"{_base_context(titulo, resumen, boe_id)}\n\n"
                "Escribe un guion de 45-60 s: 'hook' (≤3 s), 'points' (3 puntos), "
                "'cta' (cierre) y 'narration' (texto corrido para locución, natural "
                f"y sin tecnicismos, que termine mencionando la fuente {boe_id}). "
                'Devuelve JSON {"hook":..., "points":[...], "cta":..., "narration":...}.'
            ),
        },
    ]


class ValidationResult(BaseModel):
    ok: bool = Field(description="True si la pieza es publicable sin cambios.")
    cites_source: bool = Field(description="¿Cita el boe_id?")
    has_disclaimer: bool = Field(description="¿Incluye el disclaimer divulgativo?")
    faithful: bool = Field(description="¿Es fiel al resumen, sin inventar?")
    issues: list[str] = Field(default_factory=list, description="Problemas detectados.")


def validation_messages(
    channel: ContentChannel, content: str, titulo: str, resumen: str, boe_id: str
) -> list[Message]:
    return [
        {
            "role": "system",
            "content": (
                "Eres un validador editorial estricto de contenido legal divulgativo. "
                "Verificas fidelidad a la fuente (sin invenciones), presencia de cita "
                "a la fuente y de disclaimer, y adecuación al canal."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Canal: {channel.value}.\n"
                f"Fuente — título: {titulo}\nResumen: {resumen}\nId: {boe_id}\n\n"
                f"Contenido a validar:\n{content}\n\n"
                'Devuelve JSON {"ok":bool, "cites_source":bool, "has_disclaimer":bool, '
                '"faithful":bool, "issues":[...]}.'
            ),
        },
    ]
