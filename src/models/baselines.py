"""Baseline trading strategies for performance benchmarks."""

from __future__ import annotations

from datetime import date
import pandas as pd


class BuyAndHoldASPI:
    """Baseline: buy and hold benchmark index."""

    def generate_signals(self, symbols: list[str], current_date: date) -> pd.DataFrame:
        """Benchmark index buy & hold."""
        return pd.DataFrame([
            {"symbol": "ASPI", "signal": "BUY", "confidence": 1.0, "position_size_pct": 1.0}
        ])


class MomentumStrategy:
    """Baseline: Top N securities by 20-day return."""

    def __init__(self, top_n: int = 5, lookback_days: int = 20):
        self.top_n = top_n
        self.lookback_days = lookback_days

    def generate_signals(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Select top_n securities sorted by return_20d with positive momentum."""
        if features_df.empty or "return_20d" not in features_df.columns:
            return pd.DataFrame()

        filtered = features_df[features_df["return_20d"] > 0].copy()
        if filtered.empty:
            return pd.DataFrame()

        top = filtered.sort_values(by="return_20d", ascending=False).head(self.top_n)
        weight = 1.0 / len(top)

        signals = []
        for _, row in top.iterrows():
            signals.append({
                "security_id": row.get("security_id"),
                "symbol": row.get("symbol"),
                "signal": "BUY",
                "confidence": min(float(row.get("return_20d", 0)) * 2, 0.95),
                "position_size_pct": weight,
            })
        return pd.DataFrame(signals)


class BreakoutStrategy:
    """Baseline: 20-day high breakout confirmed by above-average volume."""

    def __init__(self, volume_ratio_threshold: float = 1.5):
        self.volume_ratio_threshold = volume_ratio_threshold

    def generate_signals(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Signal BUY when price is near 52w high and volume ratio > threshold."""
        if features_df.empty:
            return pd.DataFrame()

        cond = (features_df.get("dist_from_52w_high", -1) >= -0.03) & \
               (features_df.get("volume_ratio", 0) >= self.volume_ratio_threshold)
        candidates = features_df[cond].copy()
        if candidates.empty:
            return pd.DataFrame()

        signals = []
        for _, row in candidates.iterrows():
            signals.append({
                "security_id": row.get("security_id"),
                "symbol": row.get("symbol"),
                "signal": "BUY",
                "confidence": 0.75,
                "position_size_pct": 0.10,
            })
        return pd.DataFrame(signals)
