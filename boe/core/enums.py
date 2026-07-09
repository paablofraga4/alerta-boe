"""Enumeraciones del dominio.

Centralizar estos valores evita las cadenas mágicas que hoy pueblan el código
legacy ("Nacional", "Autonómico", resúmenes por rellenar, etc.).
"""

from __future__ import annotations

from enum import StrEnum


class DocumentKind(StrEnum):
    """Origen del documento."""

    BOE = "boe"
    BORME = "borme"


class Scope(StrEnum):
    """Ámbito territorial de una publicación."""

    EUROPEO = "europeo"
    NACIONAL = "nacional"
    AUTONOMICO = "autonomico"
    OTRO = "otro"


class PipelineStage(StrEnum):
    """Etapas del pipeline de ingesta/enriquecido, en orden."""

    FETCHED = "fetched"          # metadatos del sumario en DB
    TEXT_EXTRACTED = "text"      # texto HTML/XML limpio en DB
    CLASSIFIED = "classified"    # regiones, ámbito y temas
    SUMMARIZED = "summarized"    # resúmenes LLM
    EMBEDDED = "embedded"        # vector en pgvector
    LINKED = "linked"            # referencias del grafo normativo


class StageStatus(StrEnum):
    """Estado de una etapa para un documento concreto."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReferenceType(StrEnum):
    """Tipo de relación entre normas (bloque `analisis` del BOE).

    Es la semántica del grafo normativo: el "hilo y precedentes".
    """

    MODIFICA = "modifica"
    DEROGA = "deroga"
    DESARROLLA = "desarrolla"
    PRORROGA = "prorroga"
    CORRIGE = "corrige"
    CITA = "cita"
    DE_CONFORMIDAD_CON = "de_conformidad_con"
    OTRA = "otra"

    @classmethod
    def from_boe(cls, texto: str | None) -> ReferenceType:
        """Mapea el texto libre de la API del BOE a un tipo canónico."""
        if not texto:
            return cls.OTRA
        t = texto.strip().lower()
        table = {
            "modifica": cls.MODIFICA,
            "deroga": cls.DEROGA,
            "desarrolla": cls.DESARROLLA,
            "prorroga": cls.PRORROGA,
            "prórroga": cls.PRORROGA,
            "corrige": cls.CORRIGE,
            "corrección": cls.CORRIGE,
            "cita": cls.CITA,
        }
        for key, value in table.items():
            if key in t:
                return value
        if "conformidad" in t:
            return cls.DE_CONFORMIDAD_CON
        return cls.OTRA


class ReferenceDirection(StrEnum):
    """Dirección temporal de la referencia respecto al documento fuente."""

    ANTERIOR = "anterior"    # precedente (lo que este documento referencia)
    POSTERIOR = "posterior"  # derivada (lo que referencia a este documento)


class ContentChannel(StrEnum):
    """Canal de publicación de la fábrica de contenido."""

    LINKEDIN = "linkedin"
    X = "x"
    TIKTOK = "tiktok"


class ContentStatus(StrEnum):
    """Ciclo de vida de una pieza de contenido social."""

    DRAFT = "draft"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"
