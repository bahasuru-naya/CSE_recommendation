"""create staging layer

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS staging;")

    # ── staging.trade_summary ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging.trade_summary (
            id                  BIGSERIAL       PRIMARY KEY,
            symbol              VARCHAR(20)     NOT NULL,
            name                VARCHAR(200),
            last_traded_price   NUMERIC(15,4),
            change              NUMERIC(15,4),
            change_percentage   NUMERIC(10,4),
            volume              BIGINT,
            turnover            NUMERIC(20,4),
            high                NUMERIC(15,4),
            low                 NUMERIC(15,4),
            open_price          NUMERIC(15,4),
            previous_close      NUMERIC(15,4),
            num_trades          INTEGER,
            market_cap          NUMERIC(25,4),
            trading_date        DATE            NOT NULL,
            fetched_at          TIMESTAMPTZ     NOT NULL,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(symbol, trading_date)
        );
    """)

    # ── staging.company_info ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging.company_info (
            id                  BIGSERIAL       PRIMARY KEY,
            symbol              VARCHAR(20)     NOT NULL,
            name                VARCHAR(200),
            isin                VARCHAR(20),
            sector              VARCHAR(100),
            industry            VARCHAR(100),
            market_cap          NUMERIC(25,4),
            last_traded_price   NUMERIC(15,4),
            change              NUMERIC(15,4),
            change_percentage   NUMERIC(10,4),
            beta_spsl           NUMERIC(10,4),
            beta_aspi           NUMERIC(10,4),
            shares_outstanding  BIGINT,
            listed_date         DATE,
            raw_data            JSONB,
            fetched_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            fetched_date        DATE            NOT NULL DEFAULT CURRENT_DATE,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(symbol, fetched_date)
        );
    """)

    # ── staging.chart_data ───────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging.chart_data (
            id                  BIGSERIAL       PRIMARY KEY,
            symbol              VARCHAR(20)     NOT NULL,
            stock_id            INTEGER,
            trading_date        DATE            NOT NULL,
            open_price          NUMERIC(15,4),
            high                NUMERIC(15,4),
            low                 NUMERIC(15,4),
            close_price         NUMERIC(15,4),
            volume              BIGINT,
            turnover            NUMERIC(20,4),
            num_trades          INTEGER,
            fetched_at          TIMESTAMPTZ     NOT NULL,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(symbol, trading_date)
        );
    """)

    # ── staging.market_summary ───────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging.market_summary (
            id                  BIGSERIAL       PRIMARY KEY,
            trading_date        DATE            NOT NULL UNIQUE,
            aspi_value          NUMERIC(15,4),
            aspi_change         NUMERIC(15,4),
            aspi_change_pct     NUMERIC(10,4),
            snp_value           NUMERIC(15,4),
            snp_change          NUMERIC(15,4),
            snp_change_pct      NUMERIC(10,4),
            total_turnover      NUMERIC(25,4),
            total_volume        BIGINT,
            total_trades        INTEGER,
            market_cap          NUMERIC(30,4),
            fetched_at          TIMESTAMPTZ     NOT NULL,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── staging.announcements ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging.announcements (
            id                  BIGSERIAL       PRIMARY KEY,
            announcement_id     VARCHAR(50),
            title               TEXT,
            description         TEXT,
            announcement_type   VARCHAR(50),
            company_symbol      VARCHAR(20),
            announced_date      TIMESTAMPTZ,
            raw_data            JSONB,
            fetched_at          TIMESTAMPTZ     NOT NULL,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(announcement_id)
        );
    """)

    # ── staging.sector_data ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging.sector_data (
            id                  BIGSERIAL       PRIMARY KEY,
            sector_name         VARCHAR(100)    NOT NULL,
            index_value         NUMERIC(15,4),
            change              NUMERIC(15,4),
            change_pct          NUMERIC(10,4),
            volume              BIGINT,
            turnover            NUMERIC(20,4),
            trading_date        DATE            NOT NULL,
            fetched_at          TIMESTAMPTZ     NOT NULL,
            ingested_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(sector_name, trading_date)
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS staging.sector_data CASCADE;")
    op.execute("DROP TABLE IF EXISTS staging.announcements CASCADE;")
    op.execute("DROP TABLE IF EXISTS staging.market_summary CASCADE;")
    op.execute("DROP TABLE IF EXISTS staging.chart_data CASCADE;")
    op.execute("DROP TABLE IF EXISTS staging.company_info CASCADE;")
    op.execute("DROP TABLE IF EXISTS staging.trade_summary CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS staging CASCADE;")
