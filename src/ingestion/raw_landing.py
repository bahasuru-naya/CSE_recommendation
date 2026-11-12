"""Raw landing layer: stores unmodified CSE API responses into raw.api_payloads."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RawLander:
    """Lands raw API responses into raw.api_payloads with SHA-256 deduplication."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def compute_hash(payload: Any) -> str:
        """Compute SHA-256 hash of a JSON-serializable payload."""
        canonical_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def land(
        self,
        endpoint: str,
        params: dict[str, Any] | None,
        response: Any,
        http_status: int,
        elapsed_ms: int,
    ) -> int:
        """Store raw payload into raw.api_payloads.

        Returns:
            id of the inserted or existing payload record.
        """
        payload_hash = self.compute_hash(response)
        params_json = json.dumps(params or {}, default=str)
        response_json = json.dumps(response, default=str)

        # Check if already landed with same hash recently (today)
        check_query = text("""
            SELECT id FROM raw.api_payloads
            WHERE payload_hash = :hash AND endpoint = :endpoint
              AND fetched_at >= NOW() - INTERVAL '24 hours'
            ORDER BY id DESC LIMIT 1
        """)
        row = self.session.execute(check_query, {"hash": payload_hash, "endpoint": endpoint}).fetchone()
        if row:
            logger.debug("Duplicate payload for endpoint %s with hash %s skipped", endpoint, payload_hash)
            return row[0]

        insert_query = text("""
            INSERT INTO raw.api_payloads (
                endpoint, request_params, response_payload, payload_hash,
                http_status, response_time_ms, fetched_at, ingested_at
            ) VALUES (
                :endpoint, CAST(:params AS JSONB), CAST(:payload AS JSONB), :hash,
                :http_status, :elapsed_ms, NOW(), NOW()
            ) RETURNING id
        """)
        result = self.session.execute(
            insert_query,
            {
                "endpoint": endpoint,
                "params": params_json,
                "payload": response_json,
                "hash": payload_hash,
                "http_status": http_status,
                "elapsed_ms": elapsed_ms,
            },
        )
        self.session.commit()
        payload_id = result.scalar()
        logger.info("Landed raw payload #%d for endpoint %s (%d ms)", payload_id, endpoint, elapsed_ms)
        return payload_id

    def start_run(self, endpoint: str) -> str:
        """Start an ingestion run record. Returns run_id (UUID string)."""
        run_uuid = str(uuid.uuid4())
        insert_query = text("""
            INSERT INTO raw.ingestion_runs (
                run_id, endpoint, status, records_fetched, records_landed, started_at
            ) VALUES (
                CAST(:run_id AS UUID), :endpoint, 'running', 0, 0, NOW()
            )
        """)
        self.session.execute(insert_query, {"run_id": run_uuid, "endpoint": endpoint})
        self.session.commit()
        return run_uuid

    def finish_run(
        self,
        run_id: str,
        status: str,
        records_fetched: int = 0,
        records_landed: int = 0,
        error_message: str | None = None,
    ):
        """Mark ingestion run completed."""
        update_query = text("""
            UPDATE raw.ingestion_runs
            SET status = :status,
                records_fetched = :fetched,
                records_landed = :landed,
                error_message = :error,
                finished_at = NOW()
            WHERE run_id = CAST(:run_id AS UUID)
        """)
        self.session.execute(
            update_query,
            {
                "run_id": run_id,
                "status": status,
                "fetched": records_fetched,
                "landed": records_landed,
                "error": error_message,
            },
        )
        self.session.commit()
