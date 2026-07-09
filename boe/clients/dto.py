"""DTOs de parsing de las respuestas del BOE.

Objetos intermedios y planos entre el JSON crudo del BOE y los modelos ORM.
Aislar el parsing aquí permite testearlo con fixtures reales sin tocar la DB.
"""

from __future__ import annotations

from pydantic import BaseModel

from boe.core.enums import ReferenceDirection, ReferenceType


class SummaryItem(BaseModel):
    """Una publicación del sumario diario, ya aplanada."""

    boe_id: str
    title: str
    seccion: str | None = None
    seccion_codigo: str | None = None
    departamento: str | None = None
    epigrafe: str | None = None
    url_html: str | None = None
    url_pdf: str | None = None
    url_xml: str | None = None
    pages: int | None = None


class ConsolidatedMeta(BaseModel):
    """Metadatos de una norma consolidada."""

    consolidated_id: str
    title: str
    rango: str | None = None
    departamento: str | None = None
    ambito: str | None = None
    estado: str | None = None
    fecha_disposicion: str | None = None
    fecha_publicacion: str | None = None
    fecha_vigencia: str | None = None
    vigente: bool = True
    url_html: str | None = None


class IndexBlock(BaseModel):
    """Bloque del índice de una norma (artículo/capítulo)."""

    block_id: str
    title: str
    fecha_actualizacion: str | None = None
    url: str | None = None


class ReferenceEntry(BaseModel):
    """Una referencia del bloque `analisis`: arista del grafo normativo."""

    target_boe_id: str | None = None
    target_title: str | None = None
    rel_type: ReferenceType
    direction: ReferenceDirection
    raw_text: str | None = None
