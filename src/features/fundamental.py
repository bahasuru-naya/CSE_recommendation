"""Fundamental and relative strength feature calculations."""

from __future__ import annotations

import pandas as pd


def compute_relative_strength(
    stock_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods: list[int] = [5, 20],
) -> pd.DataFrame:
    """Compute relative strength vs benchmark over multiple periods."""
    df = pd.DataFrame(index=stock_returns.index)
    aligned_stock, aligned_bench = stock_returns.align(benchmark_returns, join="left")
    aligned_bench = aligned_bench.fillna(0.0)

    for p in periods:
        stock_cum = aligned_stock.rolling(window=p, min_periods=1).sum()
        bench_cum = aligned_bench.rolling(window=p, min_periods=1).sum()
        df[f"rs_vs_benchmark_{p}d"] = stock_cum - bench_cum

    return df


def compute_liquidity_features(volume: pd.Series, turnover: pd.Series, window: int = 20) -> pd.DataFrame:
    """Compute 20-day rolling average daily volume and turnover."""
    avg_vol = volume.rolling(window=window, min_periods=1).mean()
    avg_turnover = turnover.rolling(window=window, min_periods=1).mean()
    vol_ratio = volume / avg_vol.replace(0, 1.0)

    return pd.DataFrame(
        {
            "avg_daily_volume_20d": avg_vol.fillna(0),
            "avg_daily_turnover_20d": avg_turnover.fillna(0),
            "volume_sma_20": avg_vol.fillna(0),
            "volume_ratio": vol_ratio.fillna(1.0),
        },
        index=volume.index,
    )
