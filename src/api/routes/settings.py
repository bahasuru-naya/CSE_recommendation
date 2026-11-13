"""Settings management and system configuration API."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.alerts.telegram import TelegramAlerter
from src.config import get_settings
from src.db import get_db

router = APIRouter()


class SettingUpdate(BaseModel):
    value: dict[str, Any]


class TelegramSettingsUpdate(BaseModel):
    bot_token: str | None = None
    chat_id: str = ""
    alert_time: str | None = None

    @field_validator("alert_time")
    @classmethod
    def validate_alert_time(cls, value: str | None) -> str | None:
        if value is not None:
            datetime.strptime(value, "%H:%M")
        return value


@router.get("/")
def get_all_settings(db: Session = Depends(get_db)):
    """Retrieve all configuration keys and values from app.settings."""
    query = text("SELECT key, value, description, updated_at FROM app.settings WHERE key != 'telegram'")
    rows = db.execute(query).fetchall()
    return {
        r[0]: {
            "value": r[1],
            "description": r[2],
            "updated_at": r[3].isoformat() if r[3] else None,
        }
        for r in rows
    }


@router.get("/telegram")
def get_telegram_settings(db: Session = Depends(get_db)):
    """Return Telegram configuration without disclosing the bot token."""
    stored = db.execute(
        text("SELECT value FROM app.settings WHERE key = 'telegram'")
    ).scalar()
    value = stored if isinstance(stored, dict) else {}
    config = get_settings()
    bot_token = value.get("bot_token") or config.telegram_bot_token
    return {
        "bot_token_configured": bool(bot_token),
        "chat_id": value.get("chat_id") or config.telegram_chat_id,
        "alert_time": value.get("alert_time", "15:00"),
    }


@router.put("/telegram")
def update_telegram_settings(
    payload: TelegramSettingsUpdate,
    db: Session = Depends(get_db),
):
    """Save Telegram settings while retaining the token when its field is blank."""
    current = db.execute(
        text("SELECT value FROM app.settings WHERE key = 'telegram'")
    ).scalar()
    current_value = current if isinstance(current, dict) else {}
    bot_token = (payload.bot_token or "").strip() or current_value.get("bot_token", "")
    token_configured = bool(bot_token or get_settings().telegram_bot_token)
    alert_time = payload.alert_time or current_value.get("alert_time", "15:00")
    value = {
        **current_value,
        "bot_token": bot_token,
        "chat_id": payload.chat_id.strip(),
        "alert_time": alert_time,
    }
    db.execute(
        text("""
            INSERT INTO app.settings (key, value, description, updated_at)
            VALUES ('telegram', CAST(:value AS JSONB), 'Telegram alert settings', NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """),
        {"value": json.dumps(value)},
    )
    db.commit()
    return {
        "status": "updated",
        "bot_token_configured": token_configured,
        "chat_id": value["chat_id"],
        "alert_time": alert_time,
    }


@router.post("/telegram/test")
def send_telegram_test(payload: TelegramSettingsUpdate, db: Session = Depends(get_db)):
    """Send a one-off test alert using saved or currently entered credentials."""
    alerter = TelegramAlerter(
        bot_token=payload.bot_token or None,
        chat_id=payload.chat_id or None,
        db=db,
    )
    if not alerter.bot_token or not alerter.chat_id:
        raise HTTPException(status_code=400, detail="Configure a bot token and chat ID first.")
    if not alerter.send_message("CSE Recommendation: Telegram test alert sent successfully."):
        raise HTTPException(status_code=502, detail="Telegram rejected the test alert. Check the bot token and chat ID.")
    return {"status": "sent"}


@router.put("/{key}")
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)):
    """Update or insert a configuration entry."""
    query = text("""
        INSERT INTO app.settings (key, value, updated_at)
        VALUES (:key, CAST(:val AS JSONB), NOW())
        ON CONFLICT (key) DO UPDATE SET
            value = EXCLUDED.value,
            updated_at = NOW()
        RETURNING key
    """)
    res = db.execute(query, {"key": key, "val": json.dumps(payload.value)}).scalar()
    db.commit()
    if not res:
        raise HTTPException(status_code=500, detail="Failed to save setting")
    return {"status": "updated", "key": key, "new_value": payload.value}


@router.get("/jobs")
def get_scheduled_jobs(db: Session = Depends(get_db)):
    """List scheduled jobs and their enabled status."""
    query = text("""
        SELECT job_id, job_name, schedule_type, is_enabled, last_run_at, next_run_at
        FROM app.jobs
    """)
    rows = db.execute(query).fetchall()
    if not rows:
        # Return standard defaults if jobs table not yet populated
        return [
            {
                "job_id": "intraday_snapshot",
                "job_name": "Intraday Price Snapshot",
                "schedule_type": "interval_5m",
                "is_enabled": True,
            },
            {
                "job_id": "eod_fetch",
                "job_name": "EOD Ingestion & Recommendations",
                "schedule_type": "cron_14:45",
                "is_enabled": True,
            },
        ]
    return [
        {
            "job_id": r[0],
            "job_name": r[1],
            "schedule_type": r[2],
            "is_enabled": r[3],
            "last_run_at": r[4].isoformat() if r[4] else None,
            "next_run_at": r[5].isoformat() if r[5] else None,
        }
        for r in rows
    ]
