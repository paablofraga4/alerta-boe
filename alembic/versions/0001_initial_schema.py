"""Esquema inicial de AlertaBOE 2.0

Crea la extensión pgvector y el esquema completo del dominio (documentos,
versiones, grafo de referencias, resúmenes, embeddings, temas, regiones,
estado de pipeline y cola de contenido) a partir de los modelos.

Se usa `create_all` desde el metadata para garantizar que esta línea base
coincide exactamente con los modelos. Las revisiones siguientes usan
`--autogenerate` sobre esta base.

Revision ID: 0001
Revises:
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op

from boe.core.db import Base
from boe.core import models  # noqa: F401 — registra las tablas en el metadata

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
