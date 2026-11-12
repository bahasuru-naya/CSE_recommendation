"""create features layer

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS features;")

    # ── features.feature_daily ───────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS features.feature_daily (
            security_id             INTEGER         NOT NULL
                                        REFERENCES core.dim_security(security_id),
            trading_date            DATE            NOT NULL,
            feature_version         INTEGER         NOT NULL DEFAULT 1,

            -- Price features (returns)
            return_1d               NUMERIC(10,6),
            return_5d               NUMERIC(10,6),
            return_10d              NUMERIC(10,6),
            return_20d              NUMERIC(10,6),

            -- Moving averages
            sma_5                   NUMERIC(15,4),
            sma_10                  NUMERIC(15,4),
            sma_20                  NUMERIC(15,4),
            sma_50                  NUMERIC(15,4),
            sma_100                 NUMERIC(15,4),
            ema_12                  NUMERIC(15,4),
            ema_26                  NUMERIC(15,4),

            -- Momentum indicators
            rsi_14                  NUMERIC(10,4),
            macd                    NUMERIC(15,6),
            macd_signal             NUMERIC(15,6),
            macd_histogram          NUMERIC(15,6),
            stochastic_k            NUMERIC(10,4),
            stochastic_d            NUMERIC(10,4),

            -- Volatility indicators
            atr_14                  NUMERIC(15,4),
            bollinger_upper         NUMERIC(15,4),
            bollinger_lower         NUMERIC(15,4),
            bollinger_width         NUMERIC(10,6),
            volatility_20d          NUMERIC(10,6),

            -- Volume indicators
            volume_sma_20           NUMERIC(20,4),
            volume_ratio            NUMERIC(10,4),
            obv                     NUMERIC(25,4),

            -- Relative strength
            rs_vs_aspi_5d           NUMERIC(10,6),
            rs_vs_aspi_20d          NUMERIC(10,6),
            rs_vs_sector_5d         NUMERIC(10,6),
            rs_vs_sector_20d        NUMERIC(10,6),

            -- Liquidity
            avg_daily_turnover_20d  NUMERIC(20,4),
            avg_daily_volume_20d    NUMERIC(20,4),

            -- Pattern / distance
            dist_from_52w_high      NUMERIC(10,6),
            dist_from_52w_low       NUMERIC(10,6),

            -- Regime context
            aspi_above_sma100       BOOLEAN,
            aspi_volatility_20d     NUMERIC(10,6),

            -- Meta
            as_of_date              DATE            NOT NULL,
            computed_at             TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

            PRIMARY KEY (security_id, trading_date, feature_version)
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
                    'features.feature_daily',
                    'trading_date',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE
                );
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS features.feature_daily CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS features CASCADE;")
