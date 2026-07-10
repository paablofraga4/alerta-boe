"""Validador: segunda pasada anti-alucinación sobre la pieza generada.

Combina una comprobación determinista barata (¿aparece el boe_id?) con un
juicio del LLM sobre fidelidad y disclaimer. Barato + robusto.
"""

from __future__ import annotations

from boe.content.prompts import ValidationResult, validation_messages
from boe.core.enums import ContentChannel
from boe.llm.router import LLMError, LLMRouter


async def validate(
    router: LLMRouter,
    channel: ContentChannel,
    content: str,
    *,
    titulo: str,
    resumen: str,
    boe_id: str,
) -> ValidationResult:
    # Chequeo determinista: la cita a la fuente debe estar sí o sí.
    cites_source = boe_id in content

    try:
        result = await router.complete_structured(
            validation_messages(channel, content, titulo, resumen, boe_id),
            ValidationResult,
        )
    except LLMError:
        # Si el validador LLM falla, no bloqueamos: dejamos el determinista y
        # marcamos como no-ok para revisión humana.
        return ValidationResult(
            ok=False,
            cites_source=cites_source,
            has_disclaimer=False,
            faithful=False,
            issues=["El validador LLM no estuvo disponible; requiere revisión humana."],
        )

    # La cita determinista manda sobre el juicio del modelo.
    result.cites_source = result.cites_source and cites_source
    if not cites_source:
        result.ok = False
        if "No cita la fuente (boe_id)." not in result.issues:
            result.issues.append("No cita la fuente (boe_id).")
    return result
