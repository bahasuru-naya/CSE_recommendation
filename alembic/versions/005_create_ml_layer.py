"""create ml layer

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Schema ───────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS ml;")

    # ── ml.model_registry ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS ml.model_registry (
            model_id            SERIAL          PRIMARY KEY,
            model_name          VARCHAR(100)    NOT NULL,
            model_type          VARCHAR(50)     NOT NULL,
            version             INTEGER         NOT NULL,
            hyperparameters     JSONB,
            feature_columns     JSONB,
            training_date_range JSONB,
            metrics             JSONB,
            model_binary        BYTEA,
            is_active           BOOLEAN         DEFAULT FALSE,
            promoted_at         TIMESTAMPTZ,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            UNIQUE(model_name, version)
        );
    """)

    # ── ml.training_runs ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS ml.training_runs (
            run_id              SERIAL          PRIMARY KEY,
            model_id            INTEGER
                                    REFERENCES ml.model_registry(model_id),
            train_start         DATE            NOT NULL,
            train_end           DATE            NOT NULL,
            val_start           DATE            NOT NULL,
            val_end             DATE            NOT NULL,
            n_train_samples     INTEGER,
            n_val_samples       INTEGER,
            train_metrics       JSONB,
            val_metrics         JSONB,
            feature_importance  JSONB,
            duration_seconds    NUMERIC(10,2),
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── ml.predictions ───────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS ml.predictions (
            id                  BIGSERIAL,
            model_id            INTEGER         NOT NULL
                                    REFERENCES ml.model_registry(model_id),
            security_id         INTEGER         NOT NULL,
            prediction_date     DATE            NOT NULL,
            horizon_days        INTEGER         NOT NULL DEFAULT 10,
            predicted_prob      NUMERIC(6,4),
            predicted_return    NUMERIC(10,6),
            confidence_lower    NUMERIC(10,6),
            confidence_upper    NUMERIC(10,6),
            as_of_date          DATE            NOT NULL,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, prediction_date)
        );
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
            ) THEN
                PERFORM create_hypertable(
                    'ml.predictions',
                    'prediction_date',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE
                );
            END IF;
        END
        $$;
    """)

    # ── ml.backtests ─────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS ml.backtests (
            backtest_id         SERIAL          PRIMARY KEY,
            model_id            INTEGER
                                    REFERENCES ml.model_registry(model_id),
            strategy_name       VARCHAR(100),
            test_start          DATE            NOT NULL,
            test_end            DATE            NOT NULL,
            initial_capital     NUMERIC(20,4),
            final_capital       NUMERIC(20,4),
            total_return        NUMERIC(10,6),
            annualized_return   NUMERIC(10,6),
            sharpe_ratio        NUMERIC(10,4),
            max_drawdown        NUMERIC(10,6),
            win_rate            NUMERIC(6,4),
            total_trades        INTEGER,
            avg_holding_days    NUMERIC(10,2),
            turnover            NUMERIC(10,4),
            benchmark_return    NUMERIC(10,6),
            excess_return       NUMERIC(10,6),
            cost_assumptions    JSONB,
            daily_returns       JSONB,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
        );
    """)

    # ── ml.drift_metrics ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS ml.drift_metrics (
            id                  SERIAL,
            model_id            INTEGER         NOT NULL
                                    REFERENCES ml.model_registry(model_id),
            check_date          DATE            NOT NULL,
            feature_name        VARCHAR(100),
            metric_name         VARCHAR(50),
            metric_value        NUMERIC(15,6),
            alert_threshold     NUMERIC(15,6),
            is_alert            BOOLEAN         DEFAULT FALSE,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, check_date)
        );
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
            ) THEN
                PERFORM create_hypertable(
                    'ml.drift_metrics',
                    'check_date',
                    if_not_exists => TRUE,
                    migrate_data  => TRUE
                );
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ml.drift_metrics CASCADE;")
    op.execute("DROP TABLE IF EXISTS ml.backtests CASCADE;")
    op.execute("DROP TABLE IF EXISTS ml.predictions CASCADE;")
    op.execute("DROP TABLE IF EXISTS ml.training_runs CASCADE;")
    op.execute("DROP TABLE IF EXISTS ml.model_registry CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS ml CASCADE;")
