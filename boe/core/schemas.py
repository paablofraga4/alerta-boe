"""Esquemas Pydantic de la API pública (modelos de lectura).

Separan la representación externa (lo que devuelve `/v1`) del modelo ORM.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from boe.core.enums import (
    ContentChannel,
    ContentStatus,
    NotificationChannel,
    ReferenceDirection,
    ReferenceType,
    Scope,
)


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
    # Brief estructurado del agente por documento (qué regula, a quién afecta,
    # puntos_clave, plazos, que_hacer). Nulo en resúmenes v1.
    structured: dict | None = None


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


class TopicCountOut(BaseModel):
    """Tema con su número de publicaciones (para chips y navegación)."""

    name: str
    slug: str
    count: int


class TopicListResponse(BaseModel):
    topics: list[TopicCountOut] = []


# ─── Búsqueda ────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str = ""
    fecha: date | None = None
    desde: date | None = None
    hasta: date | None = None
    scope: Scope | None = None
    topic: str | None = None
    region: str | None = None
    departamento: str | None = None
    limit: int = 20


class SearchHitOut(BaseModel):
    document: DocumentOut
    score: float
    matched: list[str] = []


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchHitOut] = []


# ─── Digest del día ──────────────────────────────────────────────────────────


class DigestItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    boe_id: str
    title: str
    departamento: str | None = None
    scope: Scope
    short: str | None = None       # resumen breve, si existe
    url_html: str | None = None


class DigestGroup(BaseModel):
    scope: Scope
    count: int
    items: list[DigestItem] = []


class DigestOut(BaseModel):
    fecha: date
    total: int
    highlights: list[DigestItem] = []
    groups: list[DigestGroup] = []


# ─── Chat RAG ────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    fecha: date | None = None
    scope: Scope | None = None
    top_k: int | None = None


class Citation(BaseModel):
    boe_id: str
    title: str
    url_html: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []


# ─── Fábrica de contenido ────────────────────────────────────────────────────


class ContentPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    boe_id: str | None = None
    channel: ContentChannel
    status: ContentStatus
    script: str | None = None
    interest_score: float | None = None
    asset_path: str | None = None
    external_id: str | None = None
    published_at: datetime | None = None
    metrics: dict | None = None


class ContentListResponse(BaseModel):
    total: int
    posts: list[ContentPostOut] = []


# ─── Alertas / suscripciones (F6) ────────────────────────────────────────────


class SubscriptionCreate(BaseModel):
    email: str
    channel: NotificationChannel = NotificationChannel.EMAIL
    # Destino de entrega: email o chat_id de Telegram. Si falta y el canal es
    # email, se usa `email`.
    destination: str | None = None
    topic_slug: str | None = None
    region_name: str | None = None
    scope: Scope | None = None
    keyword: str | None = None


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: NotificationChannel
    destination: str
    topic_slug: str | None = None
    region_name: str | None = None
    scope: Scope | None = None
    keyword: str | None = None
    active: bool


class SubscriptionListResponse(BaseModel):
    total: int
    subscriptions: list[SubscriptionOut] = []
