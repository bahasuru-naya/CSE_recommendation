"""create app layer

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS app;")

    # ── app.recommendations ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.recommendations (
            id                  BIGSERIAL       PRIMARY KEY,
            security_id         INTEGER         NOT NULL,
            symbol              VARCHAR(20)     NOT NULL,
            security_name       VARCHAR(200),
            recommendation_date DATE            NOT NULL,
            signal              VARCHAR(10)     NOT NULL,
            confidence          NUMERIC(6,4),
            entry_price_low     NUMERIC(15,4),
            entry_price_high    NUMERIC(15,4),
            stop_loss           NUMERIC(15,4),
            target_price        NUMERIC(15,4),
            position_size_pct   NUMERIC(6,4),
            max_quantity        INTEGER,
            horizon_days        INTEGER         DEFAULT 10,
            reasons             JSONB,
            model_version       VARCHAR(50),
            data_freshness      JSONB,
            logo_url            VARCHAR(500),
            expires_at          TIMESTAMPTZ,
            status              VARCHAR(20)     DEFAULT 'active',
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── app.portfolio_positions ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.portfolio_positions (
            id                  SERIAL          PRIMARY KEY,
            security_id         INTEGER         NOT NULL,
            symbol              VARCHAR(20)     NOT NULL,
            side                VARCHAR(10)     DEFAULT 'LONG',
            entry_date          DATE            NOT NULL,
            entry_price         NUMERIC(15,4)   NOT NULL,
            quantity            INTEGER         NOT NULL,
            current_price       NUMERIC(15,4),
            stop_loss           NUMERIC(15,4),
            target_price        NUMERIC(15,4),
            exit_date           DATE,
            exit_price          NUMERIC(15,4),
            pnl                 NUMERIC(20,4),
            pnl_pct             NUMERIC(10,6),
            status              VARCHAR(20)     DEFAULT 'open',
            notes               TEXT,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── app.watchlist ────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.watchlist (
            id                  SERIAL          PRIMARY KEY,
            security_id         INTEGER         NOT NULL,
            symbol              VARCHAR(20)     NOT NULL,
            added_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            reason              TEXT,
            alert_price_above   NUMERIC(15,4),
            alert_price_below   NUMERIC(15,4),
            is_active           BOOLEAN         DEFAULT TRUE
        );
    """)

    # ── app.settings ─────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.settings (
            key                 VARCHAR(100)    PRIMARY KEY,
            value               JSONB           NOT NULL,
            description         TEXT,
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # Default settings
    op.execute("""
        INSERT INTO app.settings (key, value, description) VALUES
        (
            'trading_costs',
            '{"commission_pct": 0.0115, "sec_levy_pct": 0.0015, "cse_levy_pct": 0.0004}',
            'Trading cost assumptions for CSE'
        ),
        (
            'liquidity_filter',
            '{"min_avg_daily_turnover_20d": 500000, "min_avg_daily_volume_20d": 1000}',
            'Minimum liquidity for recommendations'
        ),
        (
            'risk_limits',
            '{"max_position_pct": 0.10, "max_positions": 10, "max_volume_pct": 0.05}',
            'Position sizing and risk limits'
        ),
        (
            'model_config',
            '{"horizon_days": 10, "min_excess_return": 0.02, "retrain_interval_days": 7}',
            'ML model configuration'
        ),
        (
            'scheduler',
            '{"intraday_interval_minutes": 5, "eod_fetch_time": "14:45", "recommendation_time": "15:00", "catch_up_on_startup": true}',
            'Scheduler configuration'
        ),
        (
            'data_freshness',
            '{"max_stale_days": 2, "kill_switch_enabled": true}',
            'Data freshness and kill switch settings'
        )
        ON CONFLICT (key) DO NOTHING;
    """)

    # ── app.jobs ─────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.jobs (
            job_id              VARCHAR(100)    PRIMARY KEY,
            job_name            VARCHAR(200)    NOT NULL,
            schedule_type       VARCHAR(20),
            schedule_config     JSONB,
            is_enabled          BOOLEAN         DEFAULT TRUE,
            last_run_at         TIMESTAMPTZ,
            next_run_at         TIMESTAMPTZ,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── app.job_runs ─────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.job_runs (
            id                  BIGSERIAL       PRIMARY KEY,
            job_id              VARCHAR(100)    REFERENCES app.jobs(job_id),
            status              VARCHAR(20)     NOT NULL DEFAULT 'running',
            started_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            finished_at         TIMESTAMPTZ,
            duration_seconds    NUMERIC(10,2),
            records_processed   INTEGER,
            error_message       TEXT,
            metadata            JSONB
        );
    """)

    # ── app.audit_log ────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS app.audit_log (
            id                  BIGSERIAL       PRIMARY KEY,
            action              VARCHAR(50)     NOT NULL,
            entity_type         VARCHAR(50),
            entity_id           VARCHAR(100),
            details             JSONB,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app.audit_log CASCADE;")
    op.execute("DROP TABLE IF EXISTS app.job_runs CASCADE;")
    op.execute("DROP TABLE IF EXISTS app.jobs CASCADE;")
    op.execute("DROP TABLE IF EXISTS app.settings CASCADE;")
    op.execute("DROP TABLE IF EXISTS app.watchlist CASCADE;")
    op.execute("DROP TABLE IF EXISTS app.portfolio_positions CASCADE;")
    op.execute("DROP TABLE IF EXISTS app.recommendations CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS app CASCADE;")
