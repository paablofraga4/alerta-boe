"""Triaje editorial: documents.category + documents.relevance

Categoría ciudadana (normas/ayudas/oposiciones/...) y relevancia 0-100 para
ordenar la portada y colapsar el ruido. Idempotente (IF NOT EXISTS).

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS category VARCHAR(32)")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS relevance INTEGER")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_category ON documents (category)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_relevance ON documents (relevance)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_documents_relevance")
    op.execute("DROP INDEX IF EXISTS ix_documents_category")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS relevance")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS category")
