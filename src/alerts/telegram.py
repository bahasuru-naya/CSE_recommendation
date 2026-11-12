"""Telegram alerting client for recommendations and system notifications."""

from __future__ import annotations

import logging
from typing import Any

import requests

from src.config import get_settings

logger = logging.getLogger(__name__)


class TelegramAlerter:
    """Dispatches markdown notifications to a Telegram chat or channel."""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        settings = get_settings()
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

    def send_message(self, text: str) -> bool:
        """Send a plain or markdown formatted message."""
        if not self.bot_token or not self.chat_id:
            logger.info("[Telegram Not Configured] Would send: %s", text)
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}

        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error("Failed sending Telegram alert: %s", e)
            return False

    def send_recommendation(self, rec: dict[str, Any]) -> bool:
        """Format and broadcast stock recommendation."""
        signal = rec.get("signal", "WATCH")
        symbol = rec.get("symbol")
        name = rec.get("security_name", "")
        conf = int((rec.get("confidence") or 0.5) * 100)

        lines = [
            f"*CSE SIGNAL: [{signal}] {symbol}*",
            f"_{name}_",
            f"• Confidence: `{conf}%`",
            f"• Entry Range: `LKR {rec.get('entry_price_low')} - {rec.get('entry_price_high')}`",
            f"• Stop Loss: `LKR {rec.get('stop_loss')}`",
            f"• Target Price: `LKR {rec.get('target_price')}`",
            f"• Max Qty: `{rec.get('max_quantity')} shares` ({int((rec.get('position_size_pct') or 0.05)*100)}% allocation)",
            f"• Horizon: `{rec.get('horizon_days', 10)} trading days`",
        ]
        return self.send_message("\n".join(lines))
