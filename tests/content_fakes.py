"""Router LLM falso para los tests de la fábrica de contenido.

Devuelve salidas estructuradas canónicas según el schema pedido, incluyendo el
boe_id extraído del prompt (para que pase el chequeo determinista de citas).
"""

from __future__ import annotations

import re

from boe.content.prompts import (
    LinkedInPost,
    TikTokScript,
    ValidationResult,
    XThread,
)

_BOE_RE = re.compile(r"BOE-[A-Z]-\d{4}-\d+")
_DISCLAIMER = "Esto es información divulgativa, no asesoramiento legal."


class FakeContentRouter:
    has_provider = True

    async def complete_structured(self, messages, schema):
        text = " ".join(m["content"] for m in messages)
        match = _BOE_RE.search(text)
        boe_id = match.group(0) if match else "BOE-A-2024-0001"

        if schema is LinkedInPost:
            return LinkedInPost(
                text=f"Gancho potente. 3 claves de por qué importa. {_DISCLAIMER} "
                f"Fuente [{boe_id}]."
            )
        if schema is XThread:
            return XThread(
                tweets=[
                    f"🧵 Novedad del BOE que te afecta [{boe_id}]",
                    "Clave 1 y clave 2 explicadas claro.",
                    f"Fuente [{boe_id}]. {_DISCLAIMER}",
                ]
            )
        if schema is TikTokScript:
            return TikTokScript(
                hook="¿Sabías esto del BOE?",
                points=["Punto uno", "Punto dos", "Punto tres"],
                cta="Síguenos para más",
                narration=(
                    f"El Gobierno ha aprobado una medida que te afecta. "
                    f"Te lo cuento en un minuto. Fuente {boe_id}."
                ),
            )
        if schema is ValidationResult:
            return ValidationResult(
                ok=True, cites_source=True, has_disclaimer=True, faithful=True, issues=[]
            )
        raise AssertionError(f"schema inesperado: {schema}")
