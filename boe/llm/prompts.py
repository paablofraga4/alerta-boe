"""Prompts versionados del producto.

Se conservan (y mejoran) los prompts del código legacy `summarizer_groq.py`.
Cambio clave: donde antes había DOS llamadas separadas (resumen largo y breve)
con `time.sleep(2.1)` hardcodeado, ahora hay UNA sola llamada con salida JSON
estructurada. La versión de prompt se guarda junto al resultado (`Summary`).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from boe.llm.router import Message

PROMPT_VERSION = "v1"


class SummaryOutput(BaseModel):
    """Salida estructurada de la etapa de resumen."""

    long: str = Field(description="Resumen claro y accesible, sin tecnicismos.")
    short: str = Field(description="Alerta breve (máx. 300 caracteres) con sujeto claro.")
    hook: str = Field(description="Gancho de una frase para vídeo/redes (<120 caracteres).")


def summary_messages(texto: str, titulo: str) -> list[Message]:
    """Genera resumen largo + breve + gancho en una única llamada JSON."""
    return [
        {
            "role": "system",
            "content": (
                "Eres un asistente legal experto en legislación española que explica "
                "el BOE a ciudadanos y autónomos. Escribes claro, sin tecnicismos, "
                "y nunca inventas datos que no estén en el texto."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Título de la publicación: {titulo}\n\n"
                f"Texto (puede venir recortado):\n{texto[:3500]}\n\n"
                "Devuelve EXCLUSIVAMENTE un JSON con las claves:\n"
                '  "long": resumen claro. Indica qué regula, a quién afecta, fechas '
                "importantes y qué deben hacer ciudadanos o pequeñas empresas.\n"
                '  "short": alerta de máx. 300 caracteres. Di siempre quién actúa '
                "(El Gobierno, Hacienda, la Xunta...). Evita 'se aprueba', 'se nombra'.\n"
                '  "hook": una frase gancho de menos de 120 caracteres para redes.\n'
            ),
        },
    ]


class ClassificationOutput(BaseModel):
    """Clasificación temática multi-etiqueta."""

    topics: list[str] = Field(default_factory=list)


def classification_messages(texto: str, taxonomy: list[str]) -> list[Message]:
    joined = ", ".join(taxonomy)
    return [
        {
            "role": "system",
            "content": "Clasificas publicaciones del BOE en categorías temáticas.",
        },
        {
            "role": "user",
            "content": (
                f"Categorías permitidas: {joined}.\n\n"
                f"Texto: {texto[:2000]}\n\n"
                'Devuelve un JSON {"topics": [...]} con las categorías aplicables '
                "(solo de la lista permitida; puede ser vacío)."
            ),
        },
    ]
