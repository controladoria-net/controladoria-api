from __future__ import annotations

from logging.config import fileConfig
from os import environ
from typing import Any, Dict

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.infra.database.base import Base
from src.infra.database.config import get_database_url
from src.infra.database import models  # noqa: F401  # ensure models are imported

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")
    if sqlalchemy_url and "%(sqlalchemy_url)s" not in sqlalchemy_url:
        return sqlalchemy_url
    return get_database_url()


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration: Dict[str, Any] = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
