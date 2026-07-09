"""Esquemas Pydantic de la API pública (modelos de lectura).

Separan la representación externa (lo que devuelve `/v1`) del modelo ORM.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from boe.core.enums import ReferenceDirection, ReferenceType, Scope


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    slug: str


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    code: str | None = None


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    long: str | None = None
    short: str | None = None
    hook: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    boe_id: str
    published_at: date
    title: str
    seccion: str | None = None
    departamento: str | None = None
    epigrafe: str | None = None
    rango: str | None = None
    scope: Scope
    url_html: str | None = None
    url_pdf: str | None = None
    consolidated_id: str | None = None
    topics: list[TopicOut] = []
    regions: list[RegionOut] = []


class DocumentDetailOut(DocumentOut):
    summaries: list[SummaryOut] = []


class ReferenceOut(BaseModel):
    """Una arista del hilo normativo."""

    model_config = ConfigDict(from_attributes=True)

    rel_type: ReferenceType
    direction: ReferenceDirection
    target_boe_id: str | None = None
    target_title: str | None = None
    raw_text: str | None = None


class ThreadOut(BaseModel):
    """El hilo de una publicación: precedentes y derivadas."""

    boe_id: str
    title: str
    anteriores: list[ReferenceOut] = []
    posteriores: list[ReferenceOut] = []
