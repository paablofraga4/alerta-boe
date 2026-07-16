"""Brief estructurado del agente por documento: summaries.structured

Añade una columna JSONB `structured` a `summaries` para guardar el brief rico
(qué regula, a quién afecta, puntos clave, plazos, qué hacer) que produce el
agente por documento. Idempotente: usa ADD COLUMN IF NOT EXISTS.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('ALTER TABLE summaries ADD COLUMN IF NOT EXISTS structured JSONB')


def downgrade() -> None:
    op.execute('ALTER TABLE summaries DROP COLUMN IF EXISTS structured')
