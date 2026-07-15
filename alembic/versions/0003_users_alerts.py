"""Usuarios y alertas (F6): users, subscriptions, notifications

Crea las tablas de F6. Usa create_all sobre el metadata filtrado a esas tablas,
para que coincida exactamente con los modelos (checkfirst evita recrear lo ya
existente en una DB que venga de una 0002 previa).

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-13
"""

from collections.abc import Sequence

from alembic import op
from boe.core import models  # noqa: F401 — registra las tablas
from boe.core.db import Base

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ["users", "subscriptions", "notifications"]


def upgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in _TABLES]
    Base.metadata.create_all(bind=bind, tables=tables, checkfirst=True)


def downgrade() -> None:
    # Explícito (no drop_all): drop_all sobre un subconjunto dispara el borrado
    # de TODOS los tipos ENUM del metadata (footgun de SQLAlchemy). Aquí solo se
    # tocan las tablas y los tipos ENUM propios de F6.
    for table in reversed(_TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    for enum_name in (
        "notification_status",
        "notification_channel_delivery",
        "notification_channel",
        "subscription_scope",
    ):
        op.execute(f'DROP TYPE IF EXISTS "{enum_name}" CASCADE')
