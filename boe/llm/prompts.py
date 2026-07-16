"""Prompts versionados del producto.

Se conservan (y mejoran) los prompts del código legacy `summarizer_groq.py`.
Cambio clave: donde antes había DOS llamadas separadas (resumen largo y breve)
con `time.sleep(2.1)` hardcodeado, ahora hay UNA sola llamada con salida JSON
estructurada. La versión de prompt se guarda junto al resultado (`Summary`).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from boe.llm.router import Message

# v1: resumen simple (long/short/hook) sobre 3500 chars.
# v2: agente por documento que LEE EL TEXTO COMPLETO (map-reduce) y devuelve un
#     brief estructurado (qué regula, a quién afecta, puntos clave, plazos...).
PROMPT_VERSION = "v2"


class SummaryOutput(BaseModel):
    """Salida estructurada de la etapa de resumen (compatibilidad v1)."""

    long: str = Field(description="Resumen claro y accesible, sin tecnicismos.")
    short: str = Field(description="Alerta breve (máx. 300 caracteres) con sujeto claro.")
    hook: str = Field(description="Gancho de una frase para vídeo/redes (<120 caracteres).")


class Plazo(BaseModel):
    """Una fecha/plazo relevante con la acción asociada."""

    fecha: str = Field(description="Cuándo: fecha o plazo tal como aparece en el texto.")
    accion: str = Field(description="Qué ocurre o qué hay que hacer para esa fecha.")


class DocumentBrief(BaseModel):
    """Brief completo de una publicación del BOE, leyéndola entera.

    Es la salida del agente por documento. `long/short/hook` mantienen la
    compatibilidad con el resumen v1; el resto son campos estructurados que la
    web muestra como una ficha 'en claro'.
    """

    long: str = Field(
        description="Resumen extenso y claro, varios párrafos separados por línea en blanco."
    )
    short: str = Field(description="Alerta breve (máx. 300 caracteres) con sujeto claro.")
    hook: str = Field(description="Gancho de una frase para vídeo/redes (<120 caracteres).")

    que_regula: str = Field(
        default="", description="En una frase, qué regula o establece la norma."
    )
    a_quien_afecta: list[str] = Field(
        default_factory=list, description="Colectivos afectados (autónomos, funcionarios...)."
    )
    puntos_clave: list[str] = Field(
        default_factory=list, description="Puntos clave, uno por idea. 3-6 elementos."
    )
    plazos: list[Plazo] = Field(
        default_factory=list, description="Fechas y plazos relevantes con su acción."
    )
    que_hacer: list[str] = Field(
        default_factory=list,
        description="Acciones concretas que un ciudadano o pyme debería valorar. Puede ir vacío.",
    )


_AGENT_SYSTEM = (
    "Eres un analista legal experto en legislación española que explica el BOE a "
    "ciudadanos y autónomos. Escribes claro, en lenguaje natural y sin tecnicismos. "
    "Trabajas SOLO con el texto que se te da: nunca inventas cifras, fechas ni normas."
)


def map_messages(fragmento: str, titulo: str, parte: int, total: int) -> list[Message]:
    """Etapa 'map': extrae los hechos de UN fragmento de un documento largo.

    Devuelve prosa (no JSON): se concatenará con los demás fragmentos y se
    reducirá después. Así el agente 'lee' documentos que no caben en una llamada.
    """
    return [
        {"role": "system", "content": _AGENT_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Publicación: {titulo}\n"
                f"Estás leyendo el fragmento {parte} de {total} de un documento largo.\n\n"
                f"Fragmento:\n{fragmento}\n\n"
                "Extrae en viñetas los hechos relevantes de ESTE fragmento: qué se "
                "regula, a quién afecta, importes, fechas y plazos, obligaciones y "
                "requisitos. Sé fiel al texto y conciso. No repitas el título."
            ),
        },
    ]


def brief_messages(texto: str, titulo: str) -> list[Message]:
    """Etapa 'reduce': genera el brief estructurado a partir del texto (o de los
    hechos ya extraídos de los fragmentos)."""
    return [
        {"role": "system", "content": _AGENT_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Título de la publicación: {titulo}\n\n"
                f"Texto/hechos de la publicación:\n{texto}\n\n"
                "Devuelve EXCLUSIVAMENTE un JSON con estas claves:\n"
                '  "long": resumen extenso y claro (varios párrafos separados por una '
                "línea en blanco). Explica el contexto, qué regula, a quién afecta, las "
                "fechas clave y sus consecuencias prácticas. Que se pueda leer de corrido.\n"
                '  "short": alerta de máx. 300 caracteres. Di siempre quién actúa '
                "(El Gobierno, Hacienda, la Xunta...). Evita 'se aprueba', 'se nombra'.\n"
                '  "hook": frase gancho de menos de 120 caracteres para redes.\n'
                '  "que_regula": una sola frase con lo esencial.\n'
                '  "a_quien_afecta": lista de colectivos afectados.\n'
                '  "puntos_clave": lista de 3 a 6 ideas clave, una por elemento.\n'
                '  "plazos": lista de objetos {"fecha": ..., "accion": ...} con las '
                "fechas o plazos relevantes (vacía si no hay).\n"
                '  "que_hacer": lista de acciones concretas para ciudadano o pyme '
                "(vacía si no procede).\n"
                "No inventes nada que no esté en el texto."
            ),
        },
    ]


def summary_messages(texto: str, titulo: str) -> list[Message]:
    """Compatibilidad v1: resumen largo + breve + gancho en una única llamada."""
    return [
        {
            "role": "system",
            "content": _AGENT_SYSTEM,
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


def rag_messages(question: str, contexts: list[tuple[str, str, str]]) -> list[Message]:
    """Chat RAG con citas OBLIGATORIAS.

    `contexts` es una lista de (boe_id, título, texto). El sistema exige que la
    respuesta se apoye solo en el contexto y cite los boe_id entre corchetes,
    para evitar alucinaciones en un dominio legal.
    """
    bloques = "\n\n".join(
        f"[{boe_id}] {titulo}\n{texto[:1500]}" for boe_id, titulo, texto in contexts
    )
    return [
        {
            "role": "system",
            "content": (
                "Eres un asistente que explica el BOE a ciudadanos y autónomos en "
                "lenguaje claro. Responde ÚNICAMENTE con la información del contexto. "
                "Si el contexto no basta, dilo con honestidad. Cita siempre las "
                "fuentes usadas con su identificador entre corchetes, p. ej. "
                "[BOE-A-2024-0001]. No inventes normas ni cifras. No des "
                "asesoramiento legal vinculante."
            ),
        },
        {
            "role": "user",
            "content": f"Contexto:\n{bloques}\n\nPregunta: {question}",
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
