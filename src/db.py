"""SQLAlchemy engine, session management, and optional async engine."""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from typing import Any

from sqlalchemy import TextClause, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings

logger = logging.getLogger(__name__)

# ── Settings ──────────────────────────────────────────────────────────────────
_settings = get_settings()

# ── Sync engine (primary) ─────────────────────────────────────────────────────
engine = create_engine(
    _settings.engine_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=(_settings.log_level == "DEBUG"),
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# ── Async engine (lazy / optional) ───────────────────────────────────────────
async_engine = None
AsyncSessionLocal = None

try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    async_engine = create_async_engine(
        _settings.async_database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=(_settings.log_level == "DEBUG"),
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
except (ImportError, Exception) as exc:
    logger.debug("Async engine not initialized (install asyncpg for async support): %s", exc)


# ── Declarative base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── Session helpers ───────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a transactional sync session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Context manager wrapper for non-FastAPI scripts (e.g. `with db_context() as s:`)
db_context = contextlib.contextmanager(get_db)


async def get_async_db():
    """Return an async context manager that yields an AsyncSession."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async engine is not configured or asyncpg is missing.")

    @contextlib.asynccontextmanager
    async def _ctx():
        session = AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    return _ctx()


# ── Raw SQL helper ────────────────────────────────────────────────────────────
def execute_raw(
    sql: str | TextClause,
    params: dict[str, Any] | None = None,
    *,
    fetch: bool = False,
) -> list[Any] | None:
    """Execute a raw SQL statement inside a session."""
    clause = text(sql) if isinstance(sql, str) else sql
    with db_context() as session:
        result = session.execute(clause, params or {})
        if fetch:
            return [dict(row._mapping) for row in result.fetchall()]
    return None
