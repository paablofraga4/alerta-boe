"""Etapa de resumen: una sola llamada LLM con salida estructurada.

Sustituye las DOS llamadas separadas del legacy (`summarizer_groq.py`) por una
única que devuelve resumen largo + breve + gancho en JSON validado.
"""

from __future__ import annotations

from boe.llm.prompts import PROMPT_VERSION, SummaryOutput, summary_messages
from boe.llm.router import LLMRouter


async def summarize(
    router: LLMRouter, texto: str, titulo: str
) -> tuple[SummaryOutput, str]:
    """Devuelve (resumen, versión_de_prompt). El texto puede ser el título si no
    hay cuerpo (muchas publicaciones del BOE se entienden solo con el titular)."""
    messages = summary_messages(texto or titulo, titulo)
    result = await router.complete_structured(messages, SummaryOutput)
    return result, PROMPT_VERSION
