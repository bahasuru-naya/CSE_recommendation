"""Application configuration — reads from .env via pydantic-settings."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Central configuration sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "postgresql://cse_user:cse_password@localhost:5432/cse_lake"

    # ── CSE API ───────────────────────────────────────────────────────────
    cse_api_base_url: str = "https://www.cse.lk/api/"

    # ── Telegram ──────────────────────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ── General ───────────────────────────────────────────────────────────
    log_level: str = "INFO"
    timezone: str = "Asia/Colombo"

    # ── Derived ───────────────────────────────────────────────────────────
    async_database_url: str = ""

    @model_validator(mode="after")
    def _derive_async_url(self) -> Self:
        """Build an asyncpg connection string from the sync URL."""
        if not self.async_database_url:
            self.async_database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self

    @property
    def engine_url(self) -> str:
        """Return the sync database URL (convenience alias)."""
        return self.database_url


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton :class:`Settings` instance."""
    return Settings()
