"""Entorno de Alembic.

La URL se pasa directamente al engine (create_engine), SIN enrutar por el
ConfigParser de Alembic. Así una contraseña con `%` (p. ej. un `#` codificado
como `%23`) no rompe con "invalid interpolation syntax". Toma el metadata de los
modelos para que `alembic revision --autogenerate` funcione en el futuro.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from boe.core import models  # noqa: F401 — registra los modelos en Base.metadata
from boe.core.config import settings
from boe.core.db import Base

config = context.config

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
    # create_engine con la URL como objeto/str: evita la interpolación de
    # ConfigParser (que trata `%` como carácter especial).
    connectable = create_engine(settings.sync_database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
