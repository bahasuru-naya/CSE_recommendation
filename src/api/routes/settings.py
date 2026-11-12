"""Settings management and system configuration API."""

from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db

router = APIRouter()


class SettingUpdate(BaseModel):
    value: dict[str, Any]


@router.get("/")
def get_all_settings(db: Session = Depends(get_db)):
    """Retrieve all configuration keys and values from app.settings."""
    query = text("SELECT key, value, description, updated_at FROM app.settings")
    rows = db.execute(query).fetchall()
    return {
        r[0]: {
            "value": r[1],
            "description": r[2],
            "updated_at": r[3].isoformat() if r[3] else None,
        }
        for r in rows
    }


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
