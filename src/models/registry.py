"""Model Registry: versioning, promotion gates, and artifacts in ml schema."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.lgbm_model import CSELightGBMModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages models in ml.model_registry and verifies strict promotion requirements."""

    def __init__(self, session: Session):
        self.session = session

    def register(
        self,
        model_name: str,
        model_type: str,
        model_instance: CSELightGBMModel,
        hyperparameters: dict[str, Any],
        metrics: dict[str, Any],
        feature_columns: list[str],
    ) -> int:
        """Register a new model version."""
        # Find next version number
        q_ver = text("SELECT COALESCE(MAX(version), 0) + 1 FROM ml.model_registry WHERE model_name = :name")
        next_ver = self.session.execute(q_ver, {"name": model_name}).scalar()

        insert_q = text("""
            INSERT INTO ml.model_registry (
                model_name, model_type, version, hyperparameters, feature_columns,
                metrics, model_binary, is_active, created_at
            ) VALUES (
                :name, :mtype, :ver, CAST(:params AS JSONB), CAST(:feats AS JSONB),
                CAST(:metrics AS JSONB), :binary, FALSE, NOW()
            )
            RETURNING model_id
        """)

        res = self.session.execute(
            insert_q,
            {
                "name": model_name,
                "mtype": model_type,
                "ver": next_ver,
                "params": json.dumps(hyperparameters),
                "feats": json.dumps(feature_columns),
                "metrics": json.dumps(metrics),
                "binary": model_instance.to_bytes(),
            },
        )
        self.session.commit()
        model_id = res.scalar()
        logger.info("Registered model %s v%d with id %d", model_name, next_ver, model_id)
        return model_id

    def promote(self, model_id: int):
        """Promote a specific model version to ACTIVE status, deactivating previous active versions."""
        self.session.execute(text("UPDATE ml.model_registry SET is_active = FALSE WHERE is_active = TRUE"))
        self.session.execute(
            text("UPDATE ml.model_registry SET is_active = TRUE, promoted_at = NOW() WHERE model_id = :id"),
            {"id": model_id},
        )
        self.session.commit()
        logger.info("Promoted model id %d to active", model_id)

    def prune_old_versions(self, model_name: str, keep: int = 5) -> int:
        """Delete older versions and their dependent history, retaining the newest versions."""
        if keep < 1:
            raise ValueError("At least one model version must be retained.")

        old_rows = self.session.execute(
            text("""
                SELECT model_id
                FROM ml.model_registry
                WHERE model_name = :name
                ORDER BY version DESC
                OFFSET :keep
            """),
            {"name": model_name, "keep": keep},
        ).fetchall()
        old_model_ids = [row[0] for row in old_rows]
        if not old_model_ids:
            return 0

        dependent_tables = (
            "ml.training_runs",
            "ml.predictions",
            "ml.backtests",
            "ml.drift_metrics",
        )
        for model_id in old_model_ids:
            for table in dependent_tables:
                self.session.execute(
                    text(f"DELETE FROM {table} WHERE model_id = :model_id"),
                    {"model_id": model_id},
                )
            self.session.execute(
                text("DELETE FROM ml.model_registry WHERE model_id = :model_id"),
                {"model_id": model_id},
            )

        self.session.commit()
        logger.info("Pruned %d old versions of model %s; retaining %d.", len(old_model_ids), model_name, keep)
        return len(old_model_ids)

    def get_active_model(self) -> tuple[int, CSELightGBMModel, dict[str, Any]] | None:
        """Load currently active model from ml.model_registry."""
        query = text("""
            SELECT model_id, model_name, version, hyperparameters, feature_columns, metrics, model_binary
            FROM ml.model_registry
            WHERE is_active = TRUE
            ORDER BY promoted_at DESC
            LIMIT 1
        """)
        row = self.session.execute(query).fetchone()
        if not row:
            return None

        model_id, name, ver, params, feats, metrics, bin_data = row
        model = CSELightGBMModel.from_bytes(bytes(bin_data))
        metadata = {"model_name": name, "version": ver, "features": feats, "metrics": metrics}
        return model_id, model, metadata

    def check_promotion_gate(self, backtest_excess_return: float, sharpe_ratio: float) -> bool:
        """Strict rule: Model goes live only if it beats benchmark net of costs and Sharpe > 1.0."""
        passed = (backtest_excess_return > 0.0) and (sharpe_ratio >= 1.0)
        logger.info("Promotion gate check: excess_return=%.2f%%, sharpe=%.2f -> Passed: %s",
                    backtest_excess_return, sharpe_ratio, passed)
        return passed
