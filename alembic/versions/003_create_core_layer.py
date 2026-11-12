"""create core layer

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS core;")

    # ── core.dim_security ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.dim_security (
            security_id         SERIAL          PRIMARY KEY,
            symbol              VARCHAR(20)     NOT NULL,
            name                VARCHAR(200),
            isin                VARCHAR(20),
            sector              VARCHAR(100),
            industry            VARCHAR(100),
            listing_date        DATE,
            delisting_date      DATE,
            is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
            share_type          VARCHAR(50),
            shares_outstanding  BIGINT,
            stock_id            INTEGER,
            logo_url            VARCHAR(500),
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(symbol)
        );
    """)

    # ── core.dim_calendar ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.dim_calendar (
            calendar_date       DATE            PRIMARY KEY,
            year                INTEGER         NOT NULL,
            quarter             INTEGER         NOT NULL,
            month               INTEGER         NOT NULL,
            day_of_week         INTEGER         NOT NULL,
            is_trading_day      BOOLEAN         NOT NULL DEFAULT TRUE,
            is_holiday          BOOLEAN         NOT NULL DEFAULT FALSE,
            holiday_name        VARCHAR(200),
            trading_day_number  INTEGER
        );
    """)

    # ── core.fact_price_daily ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.fact_price_daily (
            security_id     INTEGER         NOT NULL
                                REFERENCES core.dim_security(security_id),
            trading_date    DATE            NOT NULL,
            open            NUMERIC(15,4),
            high            NUMERIC(15,4),
            low             NUMERIC(15,4),
            close           NUMERIC(15,4),
            volume          BIGINT,
            turnover        NUMERIC(20,4),
            num_trades      INTEGER,
            vwap            NUMERIC(15,4)
                                GENERATED ALWAYS AS (
                                    CASE WHEN volume > 0
                                         THEN turnover / volume
                                         ELSE NULL
                                    END
                                ) STORED,
            adj_close       NUMERIC(15,4),
            adj_factor      NUMERIC(15,8)   DEFAULT 1.0,
            change          NUMERIC(15,4),
            change_pct      NUMERIC(10,4),
            previous_close  NUMERIC(15,4),
            is_traded       BOOLEAN         NOT NULL DEFAULT TRUE,
            data_source     VARCHAR(50),
            ingested_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            as_of_date      DATE,
            UNIQUE(security_id, trading_date)
        );
    """)

    # Convert to TimescaleDB hypertable
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
            ) THEN
                PERFORM create_hypertable(
                    'core.fact_price_daily',
                    'trading_date',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE
                );
            END IF;
        END
        $$;
    """)

    # ── core.fact_price_intraday ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.fact_price_intraday (
            security_id     INTEGER         NOT NULL
                                REFERENCES core.dim_security(security_id),
            timestamp       TIMESTAMPTZ     NOT NULL,
            price           NUMERIC(15,4),
            volume          BIGINT,
            turnover        NUMERIC(20,4)
        );
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
            ) THEN
                PERFORM create_hypertable(
                    'core.fact_price_intraday',
                    'timestamp',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE
                );
            END IF;
        END
        $$;
    """)

    # ── core.fact_index_daily ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.fact_index_daily (
            index_name      VARCHAR(50)     NOT NULL,
            trading_date    DATE            NOT NULL,
            open            NUMERIC(15,4),
            high            NUMERIC(15,4),
            low             NUMERIC(15,4),
            close           NUMERIC(15,4),
            change          NUMERIC(15,4),
            change_pct      NUMERIC(10,4),
            volume          BIGINT,
            turnover        NUMERIC(20,4),
            num_trades      INTEGER,
            UNIQUE(index_name, trading_date)
        );
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
            ) THEN
                PERFORM create_hypertable(
                    'core.fact_index_daily',
                    'trading_date',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE
                );
            END IF;
        END
        $$;
    """)

    # ── core.fact_announcement ───────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.fact_announcement (
            announcement_id     SERIAL          PRIMARY KEY,
            security_id         INTEGER
                                    REFERENCES core.dim_security(security_id),
            announcement_type   VARCHAR(50),
            title               TEXT,
            description         TEXT,
            announced_at        TIMESTAMPTZ,
            impact_score        NUMERIC(10,4),
            raw_data            JSONB,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── core.fact_corporate_action ───────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.fact_corporate_action (
            id              SERIAL          PRIMARY KEY,
            security_id     INTEGER         NOT NULL
                                REFERENCES core.dim_security(security_id),
            action_type     VARCHAR(20)     NOT NULL,
            ex_date         DATE,
            record_date     DATE,
            details         JSONB,
            adj_factor      NUMERIC(15,8),
            ingested_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── core.fact_macro ──────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.fact_macro (
            trading_date    DATE            NOT NULL,
            indicator_name  VARCHAR(100)    NOT NULL,
            value           NUMERIC(20,6),
            source          VARCHAR(100),
            ingested_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            PRIMARY KEY (trading_date, indicator_name)
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core.fact_macro CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.fact_corporate_action CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.fact_announcement CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.fact_index_daily CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.fact_price_intraday CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.fact_price_daily CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.dim_calendar CASCADE;")
    op.execute("DROP TABLE IF EXISTS core.dim_security CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS core CASCADE;")
