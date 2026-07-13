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
    import sqlalchemy as sa

    # Drop de tablas con CASCADE (orden hijo→padre) y luego de los tipos ENUM
    # propios. Evita el error de "cannot drop type ... depends on it" de
    # drop_all y no toca tipos de otros esquemas (seguro en Supabase).
    for table in reversed(Base.metadata.sorted_tables):
        op.execute(f'DROP TABLE IF EXISTS "{table.name}" CASCADE')

    enum_names: set[str] = set()
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, sa.Enum) and column.type.name:
                enum_names.add(column.type.name)
    for name in sorted(enum_names):
        op.execute(f'DROP TYPE IF EXISTS "{name}" CASCADE')

    op.execute("DROP EXTENSION IF EXISTS vector")
