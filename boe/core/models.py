"""Modelos SQLAlchemy 2.0 del dominio.

Rediseño del esquema del código legacy (`app/db/models.py`) para soportar:
  - el pipeline de ingesta por etapas con estado explícito (`PipelineState`),
  - el grafo normativo "hilo y precedentes" (`Reference`),
  - resúmenes reproducibles con trazabilidad de modelo/prompt (`Summary`),
  - búsqueda vectorial con pgvector (`Embedding`),
  - la cola de la fábrica de contenido (`ContentPost`).

Nada del esquema viejo se pierde: hay un mapeo one-shot en
`boe/ingest/migrate_legacy.py` (fase F0).
"""

from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Computed,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from boe.core.config import settings
from boe.core.db import Base
from boe.core.enums import (
    ContentChannel,
    ContentStatus,
    DocumentKind,
    PipelineStage,
    ReferenceDirection,
    ReferenceType,
    Scope,
    StageStatus,
)

# ─── Tablas de asociación (N:M) ──────────────────────────────────────────────

document_topics = Table(
    "document_topics",
    Base.metadata,
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
)

document_regions = Table(
    "document_regions",
    Base.metadata,
    Column("document_id", ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("region_id", ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ─── Documentos ──────────────────────────────────────────────────────────────


class Document(Base, TimestampMixin):
    """Una publicación del BOE/BORME. Unidad central del sistema."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    boe_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    kind: Mapped[DocumentKind] = mapped_column(
        Enum(DocumentKind, name="document_kind"), default=DocumentKind.BOE
    )

    published_at: Mapped[date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(Text)

    seccion: Mapped[str | None] = mapped_column(String(255))
    seccion_codigo: Mapped[str | None] = mapped_column(String(16))
    departamento: Mapped[str | None] = mapped_column(String(512), index=True)
    epigrafe: Mapped[str | None] = mapped_column(String(512))
    rango: Mapped[str | None] = mapped_column(String(128))

    scope: Mapped[Scope] = mapped_column(
        Enum(Scope, name="document_scope"), default=Scope.OTRO, index=True
    )

    url_html: Mapped[str | None] = mapped_column(Text)
    url_pdf: Mapped[str | None] = mapped_column(Text)
    url_xml: Mapped[str | None] = mapped_column(Text)
    pages: Mapped[int | None] = mapped_column(Integer)

    # Texto limpio del documento (rellenado en la etapa TEXT_EXTRACTED).
    full_text: Mapped[str | None] = mapped_column(Text)

    # Id en el corpus de legislación consolidada, si aplica (habilita el grafo).
    consolidated_id: Mapped[str | None] = mapped_column(String(64), index=True)

    # JSON crudo del sumario tal cual lo devolvió el BOE: reprocesable sin re-fetch.
    raw: Mapped[dict | None] = mapped_column(JSONB)

    # Vector de texto completo (español) para la búsqueda full-text. Columna
    # generada por Postgres a partir de título + cuerpo; se mantiene sola.
    search_vector = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(full_text, ''))",
            persisted=True,
        ),
        nullable=True,
    )

    # Relaciones
    topics: Mapped[list[Topic]] = relationship(
        secondary=document_topics, back_populates="documents"
    )
    regions: Mapped[list[Region]] = relationship(
        secondary=document_regions, back_populates="documents"
    )
    summaries: Mapped[list[Summary]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    stages: Mapped[list[PipelineState]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    embedding: Mapped[Embedding | None] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        Index("ix_documents_published_scope", "published_at", "scope"),
        Index("ix_documents_search", "search_vector", postgresql_using="gin"),
    )


class DocumentVersion(Base, TimestampMixin):
    """Versión consolidada de una norma (timeline de cambios de una ley)."""

    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    consolidated_id: Mapped[str] = mapped_column(String(64), index=True)
    version_label: Mapped[str | None] = mapped_column(String(128))
    fecha_vigencia: Mapped[date | None] = mapped_column(Date)
    fecha_actualizacion: Mapped[date | None] = mapped_column(Date)
    texto: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("consolidated_id", "version_label", name="uq_version"),
    )


# ─── Grafo normativo ─────────────────────────────────────────────────────────


class Reference(Base, TimestampMixin):
    """Arista del grafo: una norma referencia a otra, con tipo y dirección.

    Proviene del bloque `analisis` de la API de legislación consolidada.
    Con esta tabla, "¿qué modifica / deroga / desarrolla esta norma?" y su
    inverso se responden con un CTE recursivo sobre Postgres.
    """

    __tablename__ = "references"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Documento origen de la relación (siempre existe en nuestra DB).
    source_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    # Documento destino: puede no estar aún ingerido → guardamos su id del BOE.
    target_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    target_boe_id: Mapped[str | None] = mapped_column(String(64), index=True)
    target_title: Mapped[str | None] = mapped_column(Text)

    rel_type: Mapped[ReferenceType] = mapped_column(
        Enum(ReferenceType, name="reference_type"), default=ReferenceType.OTRA
    )
    direction: Mapped[ReferenceDirection] = mapped_column(
        Enum(ReferenceDirection, name="reference_direction")
    )
    raw_text: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Document] = relationship(foreign_keys=[source_id])
    target: Mapped[Document | None] = relationship(foreign_keys=[target_id])

    __table_args__ = (
        UniqueConstraint(
            "source_id", "target_boe_id", "rel_type", "direction", name="uq_reference"
        ),
    )


# ─── Enriquecido ─────────────────────────────────────────────────────────────


class Summary(Base, TimestampMixin):
    """Resúmenes generados por LLM, con trazabilidad para reproducibilidad."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )

    # Resumen largo accesible, resumen breve tipo alerta y gancho para vídeo.
    long: Mapped[str | None] = mapped_column(Text)
    short: Mapped[str | None] = mapped_column(Text)
    hook: Mapped[str | None] = mapped_column(Text)

    # Trazabilidad: con qué se generó (para poder regenerar o auditar).
    model: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(32))

    document: Mapped[Document] = relationship(back_populates="summaries")


class Embedding(Base):
    """Vector semántico del documento (pgvector). Un vector por documento."""

    __tablename__ = "embeddings"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    model: Mapped[str] = mapped_column(String(128))
    vector = mapped_column(Vector(settings.embeddings_dim))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped[Document] = relationship(back_populates="embedding")

    # Índice HNSW para búsqueda vectorial por distancia coseno.
    __table_args__ = (
        Index(
            "ix_embeddings_hnsw",
            "vector",
            postgresql_using="hnsw",
            postgresql_ops={"vector": "vector_cosine_ops"},
        ),
    )


class Topic(Base):
    """Categoría temática (subvención, empleo público, sanidad...)."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    documents: Mapped[list[Document]] = relationship(
        secondary=document_topics, back_populates="topics"
    )


class Region(Base):
    """Comunidad autónoma detectada en el documento."""

    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    code: Mapped[str | None] = mapped_column(String(16), unique=True)

    documents: Mapped[list[Document]] = relationship(
        secondary=document_regions, back_populates="regions"
    )


# ─── Estado del pipeline ─────────────────────────────────────────────────────


class PipelineState(Base, TimestampMixin):
    """Estado de una etapa del pipeline para un documento.

    Hace la ingesta reanudable e idempotente: se puede consultar qué documentos
    están pendientes de resumir, cuáles fallaron al embeder, etc.
    """

    __tablename__ = "pipeline_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[PipelineStage] = mapped_column(Enum(PipelineStage, name="pipeline_stage"))
    status: Mapped[StageStatus] = mapped_column(
        Enum(StageStatus, name="stage_status"), default=StageStatus.PENDING, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)

    document: Mapped[Document] = relationship(back_populates="stages")

    __table_args__ = (
        UniqueConstraint("document_id", "stage", name="uq_pipeline_stage"),
    )


# ─── Fábrica de contenido ────────────────────────────────────────────────────


class ContentPost(Base, TimestampMixin):
    """Pieza de contenido para redes, con su ciclo de aprobación y publicación."""

    __tablename__ = "content_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    channel: Mapped[ContentChannel] = mapped_column(Enum(ContentChannel, name="content_channel"))
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"), default=ContentStatus.DRAFT, index=True
    )

    script: Mapped[str | None] = mapped_column(Text)        # texto/guion generado
    asset_path: Mapped[str | None] = mapped_column(Text)    # ruta al vídeo/imagen renderizado
    external_id: Mapped[str | None] = mapped_column(String(255))  # id del post publicado
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Puntuación del curador y métricas post-publicación.
    interest_score: Mapped[float | None] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSONB)

    document: Mapped[Document | None] = relationship()
