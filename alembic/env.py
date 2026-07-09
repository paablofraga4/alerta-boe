"""Entorno de Alembic.

Usa la URL síncrona (psycopg) derivada de la config del proyecto y toma el
metadata de los modelos del dominio, para que `alembic revision --autogenerate`
detecte cambios de esquema automáticamente en las fases siguientes.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from boe.core.config import settings
from boe.core.db import Base
from boe.core import models  # noqa: F401 — registra los modelos en Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
