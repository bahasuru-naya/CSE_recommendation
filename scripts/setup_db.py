"""Database bootstrap script.

Creates the cse_lake database (if it doesn't exist), enables the TimescaleDB
extension, creates the required schemas, and runs Alembic migrations.

Usage::

    python -m scripts.setup_db
    # or
    python scripts/setup_db.py
"""

from __future__ import annotations

import logging
import subprocess
import sys
from urllib.parse import urlparse

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCHEMAS = ("raw", "staging", "core", "features", "ml", "app")


def _parse_url(url: str) -> dict[str, str | int]:
    """Extract connection parameters from a PostgreSQL URL."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username or "cse_user",
        "password": parsed.password or "cse_password",
        "dbname": (parsed.path or "/cse_lake").lstrip("/"),
    }


def _ensure_database(params: dict[str, str | int]) -> None:
    """Create the target database if it does not already exist."""
    dbname = params["dbname"]
    maintenance_params = {**params, "dbname": "postgres"}

    logger.info("Connecting to maintenance database 'postgres' …")
    conn = psycopg2.connect(**maintenance_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone()
    if exists:
        logger.info("Database '%s' already exists.", dbname)
    else:
        logger.info("Creating database '%s' …", dbname)
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
        logger.info("Database '%s' created.", dbname)

    cur.close()
    conn.close()


def _enable_timescaledb(params: dict[str, str | int]) -> None:
    """Enable the TimescaleDB extension in the target database."""
    logger.info("Enabling TimescaleDB extension …")
    conn = psycopg2.connect(**params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    logger.info("TimescaleDB extension enabled.")
    cur.close()
    conn.close()


def _create_schemas(params: dict[str, str | int]) -> None:
    """Create application schemas."""
    conn = psycopg2.connect(**params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    for schema in SCHEMAS:
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
        logger.info("Schema '%s' ready.", schema)

    # Also create the quarantine table in raw
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.quarantine (
            id          SERIAL PRIMARY KEY,
            table_name  TEXT NOT NULL,
            record      JSONB NOT NULL,
            error       TEXT NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    logger.info("raw.quarantine table ready.")

    cur.close()
    conn.close()


def _run_alembic() -> None:
    """Run ``alembic upgrade head`` to apply migrations."""
    logger.info("Running Alembic migrations …")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info("Alembic migrations applied successfully.")
        else:
            # Alembic may not be initialised yet — that's OK for initial setup
            if "Can't locate revision" in result.stderr or "No such" in result.stderr:
                logger.warning(
                    "Alembic env not initialised yet — skipping migrations. "
                    "Run 'alembic init alembic' to set up."
                )
            else:
                logger.warning("Alembic returned non-zero: %s\n%s", result.stdout, result.stderr)
    except FileNotFoundError:
        logger.warning("Alembic not found on PATH — skipping migrations.")


def main() -> None:
    """Entry point."""
    settings = get_settings()
    params = _parse_url(settings.database_url)

    logger.info("=" * 60)
    logger.info("CSE Recommendation — Database Setup")
    logger.info("=" * 60)

    _ensure_database(params)
    _enable_timescaledb(params)
    _create_schemas(params)
    _run_alembic()

    logger.info("=" * 60)
    logger.info("Database setup complete. Schemas: %s", ", ".join(SCHEMAS))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
