"""Etapa de resumen.

Delega en el agente por documento (`document_agent`), que LEE EL TEXTO COMPLETO
(map-reduce cuando es largo) y devuelve un brief estructurado. Se mantiene la
firma histórica `summarize()` para no romper llamadas existentes.
"""

from __future__ import annotations

from boe.enrich.document_agent import summarize_document
from boe.llm.prompts import DocumentBrief
from boe.llm.router import LLMRouter


async def summarize(
    router: LLMRouter, texto: str, titulo: str
) -> tuple[DocumentBrief, str]:
    """Devuelve (brief, versión_de_prompt). El texto puede ser el título si no
    hay cuerpo (muchas publicaciones del BOE se entienden solo con el titular)."""
    return await summarize_document(router, texto, titulo)
