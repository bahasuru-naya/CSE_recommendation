"""Alembic environment configuration for CSE Stock Recommendation System.

Loads DATABASE_URL from environment or .env file and runs migrations
across schemas: raw, staging, core, features, ml, app.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# ---------------------------------------------------------------------------
# Load DATABASE_URL from .env if python-dotenv is available
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    # Walk up to find .env relative to this file or the project root
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _dotenv_path = os.path.join(_project_root, ".env")
    if os.path.isfile(_dotenv_path):
        load_dotenv(_dotenv_path, override=False)
except ImportError:
    pass  # python-dotenv not installed; rely on real env vars

# Alembic Config object
config = context.config

# Override sqlalchemy.url from environment
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No SQLAlchemy MetaData object for autogenerate (we use raw SQL migrations)
target_metadata = None

# All schemas managed by this project
MANAGED_SCHEMAS = ["raw", "staging", "core", "features", "ml", "app"]


def include_name(name, type_, parent_names):
    """Filter objects to only managed schemas."""
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.  Calls to
    context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table_schema="public",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
