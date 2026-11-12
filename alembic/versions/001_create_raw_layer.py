"""create raw layer

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # ── raw.api_payloads ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS raw.api_payloads (
            id              BIGSERIAL       PRIMARY KEY,
            endpoint        VARCHAR(100)    NOT NULL,
            request_params  JSONB,
            response_payload JSONB          NOT NULL,
            payload_hash    VARCHAR(64)     NOT NULL,
            http_status     INTEGER         NOT NULL,
            response_time_ms INTEGER,
            fetched_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            ingested_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_payloads_endpoint
            ON raw.api_payloads (endpoint, fetched_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_payloads_hash
            ON raw.api_payloads (payload_hash);
    """)

    # ── raw.ingestion_runs ───────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS raw.ingestion_runs (
            id              BIGSERIAL       PRIMARY KEY,
            run_id          UUID            NOT NULL DEFAULT gen_random_uuid(),
            endpoint        VARCHAR(100)    NOT NULL,
            status          VARCHAR(20)     NOT NULL DEFAULT 'running',
            records_fetched INTEGER         DEFAULT 0,
            records_landed  INTEGER         DEFAULT 0,
            error_message   TEXT,
            started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            finished_at     TIMESTAMPTZ
        );
    """)

    # ── raw.quarantine ───────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS raw.quarantine (
            id              BIGSERIAL       PRIMARY KEY,
            source_table    VARCHAR(100),
            record_data     JSONB           NOT NULL,
            error_type      VARCHAR(50),
            error_message   TEXT,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            resolved        BOOLEAN         DEFAULT FALSE
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS raw.quarantine CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.ingestion_runs CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.api_payloads CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS raw CASCADE;")
