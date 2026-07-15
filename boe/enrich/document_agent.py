"""Agente por documento: lee la publicación ENTERA y produce un brief rico.

A diferencia del resumen v1 (una sola llamada sobre 3500 caracteres), este agente
recorre todo el `full_text`. Si el texto cabe en una llamada, genera el brief
directamente; si es largo, hace map-reduce:

    map:    trocea el texto y extrae los hechos de cada fragmento (prosa)
    reduce: sintetiza esos hechos en un brief estructurado (JSON validado)

Así el resumen "en claro" que ve el usuario está basado en el documento completo,
no en su primer párrafo.
"""

from __future__ import annotations

import structlog

from boe.llm.prompts import (
    PROMPT_VERSION,
    DocumentBrief,
    brief_messages,
    map_messages,
)
from boe.llm.router import LLMRouter

log = structlog.get_logger(__name__)

# Umbral por debajo del cual resumimos en una sola pasada (sin map-reduce).
# Un fragmento del BOE de ~7000 caracteres son ~1800 tokens: cabe de sobra en el
# contexto de los modelos que usamos.
SINGLE_PASS_CHARS = 7000
# Tamaño de cada fragmento en el map, con un pequeño solape para no cortar ideas.
CHUNK_CHARS = 6000
CHUNK_OVERLAP = 300


def chunk_text(texto: str, *, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Trocea el texto en fragmentos con solape. Corta en el salto de línea más
    cercano para no partir frases cuando es posible."""
    if len(texto) <= size:
        return [texto]
    chunks: list[str] = []
    start = 0
    n = len(texto)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # Busca un corte "limpio" (salto de línea) en el último tramo.
            corte = texto.rfind("\n", start + size - overlap, end)
            if corte != -1 and corte > start:
                end = corte
        chunks.append(texto[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


async def summarize_document(
    router: LLMRouter, full_text: str, titulo: str
) -> tuple[DocumentBrief, str]:
    """Genera el brief estructurado de una publicación leyéndola entera.

    Devuelve (brief, versión_de_prompt). Si no hay cuerpo, resume el título
    (muchas publicaciones del BOE se entienden solo con el titular).
    """
    texto = (full_text or "").strip()
    if not texto:
        brief = await _reduce(router, titulo, titulo)
        return brief, PROMPT_VERSION

    if len(texto) <= SINGLE_PASS_CHARS:
        brief = await _reduce(router, texto, titulo)
        return brief, PROMPT_VERSION

    # Documento largo: map-reduce.
    fragmentos = chunk_text(texto)
    log.info("document_agent_mapreduce", titulo=titulo[:80], fragmentos=len(fragmentos))
    hechos: list[str] = []
    for i, fragmento in enumerate(fragmentos, start=1):
        parcial = await router.complete(
            map_messages(fragmento, titulo, i, len(fragmentos)),
            temperature=0.2,
        )
        if parcial:
            hechos.append(f"[Parte {i}]\n{parcial}")
    consolidado = "\n\n".join(hechos) if hechos else texto[:SINGLE_PASS_CHARS]
    brief = await _reduce(router, consolidado, titulo)
    return brief, PROMPT_VERSION


async def _reduce(router: LLMRouter, texto: str, titulo: str) -> DocumentBrief:
    return await router.complete_structured(brief_messages(texto, titulo), DocumentBrief)
