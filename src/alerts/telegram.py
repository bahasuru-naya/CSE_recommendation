"""Telegram alerting client for recommendations and system notifications."""

from __future__ import annotations

import html
import logging
from typing import Any

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config import get_settings

logger = logging.getLogger(__name__)


class TelegramAlerter:
    """Dispatch alerts using database settings, falling back to environment config."""

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        db: Session | None = None,
    ):
        settings = get_settings()
        stored: dict[str, str] = {}
        if db is not None:
            row = db.execute(
                text("SELECT value FROM app.settings WHERE key = 'telegram'")
            ).scalar()
            if isinstance(row, dict):
                stored = row

        self.bot_token = bot_token or stored.get("bot_token") or settings.telegram_bot_token
        self.chat_id = chat_id or stored.get("chat_id") or settings.telegram_chat_id

    def send_message(self, message: str, parse_mode: str | None = None) -> bool:
        """Send a message and report Telegram API failures."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram alert skipped: bot token or chat ID is not configured.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            payload = {"chat_id": self.chat_id, "text": message}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
        except requests.RequestException as exc:
            logger.error("Telegram request failed (%s).", type(exc).__name__)
            return False
        except ValueError:
            logger.error("Telegram returned an invalid response.")
            return False

        if response.status_code != 200 or not isinstance(result, dict) or not result.get("ok"):
            error = result.get("description", "unknown error") if isinstance(result, dict) else "invalid response"
            logger.error("Telegram rejected the message (HTTP %s): %s", response.status_code, error)
            return False
        return True

    def send_recommendation(self, rec: dict[str, Any]) -> bool:
        """Format and send a stock recommendation."""
        signal = html.escape(str(rec.get("signal", "WATCH")))
        symbol = html.escape(str(rec.get("symbol") or ""))
        name = html.escape(str(rec.get("security_name") or ""))
        confidence = int((rec.get("confidence") or 0.5) * 100)
        position_size = int((rec.get("position_size_pct") or 0.05) * 100)
        message = "\n".join(
            [
                f"<b>CSE SIGNAL: [{signal}] {symbol}</b>",
                f"<i>{name}</i>",
                f"Confidence: {confidence}%",
                f"Entry Range: LKR {html.escape(str(rec.get('entry_price_low')))} - {html.escape(str(rec.get('entry_price_high')))}",
                f"Stop Loss: LKR {html.escape(str(rec.get('stop_loss')))}",
                f"Target Price: LKR {html.escape(str(rec.get('target_price')))}",
                f"Max Qty: {html.escape(str(rec.get('max_quantity')))} shares ({position_size}% allocation)",
                f"Horizon: {html.escape(str(rec.get('horizon_days', 10)))} trading days",
            ]
        )
        return self.send_message(message, parse_mode="HTML")
