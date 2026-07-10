"""Índices de búsqueda: tsvector (full-text español) + HNSW (vectorial)

Añade la columna generada `search_vector` con su índice GIN y el índice HNSW
sobre `embeddings.vector`. Idempotente (IF NOT EXISTS): la línea base 0001
crea el esquema desde los modelos, así que en una DB nueva estos objetos ya
existen y esta revisión es un no-op; en una DB que aplicó una 0001 anterior,
los crea.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(full_text, ''))
        ) STORED
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_documents_search "
        "ON documents USING gin (search_vector)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_embeddings_hnsw "
        "ON embeddings USING hnsw (vector vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embeddings_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_documents_search")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS search_vector")
