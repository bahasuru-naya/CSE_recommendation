"""Tests for the Market Regime Filter, Position Sizing, and Decision Rules."""

import pandas as pd
import pytest

from src.engine.position_sizing import PositionSizer
from src.models.backtester import CostAwareBacktester
from src.models.regime_filter import RegimeFilter


def test_regime_filter_bullish():
    """Verify Bullish regime when ASPI is above 100 SMA with low volatility."""
    rf = RegimeFilter(vol_threshold=0.28)
    res = rf.classify(aspi_close=21000.0, aspi_sma100=20000.0, aspi_volatility=0.15)
    assert res["regime"] == "BULLISH"
    assert res["allow_buy"] is True
    assert res["position_scale"] == 1.0


def test_regime_filter_bearish():
    """Verify Bearish regime when ASPI is below 100 SMA."""
    rf = RegimeFilter(vol_threshold=0.28)
    res = rf.classify(aspi_close=19500.0, aspi_sma100=20000.0, aspi_volatility=0.15)
    assert res["regime"] == "BEARISH"
    assert res["allow_buy"] is False
    assert res["position_scale"] == 0.25


def test_regime_filter_high_volatility():
    """Verify High Volatility regime halts buying regardless of trend."""
    rf = RegimeFilter(vol_threshold=0.28)
    res = rf.classify(aspi_close=22000.0, aspi_sma100=20000.0, aspi_volatility=0.35)
    assert res["regime"] == "HIGH_VOLATILITY"
    assert res["allow_buy"] is False
    assert res["position_scale"] == 0.5


def test_position_sizer_valid():
    """Verify position sizing calculates safe share count respecting limits."""
    sizer = PositionSizer(total_portfolio_value=1_000_000.0)
    # Entry = LKR 50.0, Stop = LKR 45.0 (risk per share = 5.0)
    # 2% risk = 20,000 LKR -> risk_qty = 4,000 shares
    # 10% cap = 100,000 LKR -> cap_qty = 2,000 shares
    # Volume = 10,000 shares -> 5% liq_qty = 500 shares
    # Final qty should be min(4000, 2000, 500) = 500 shares
    res = sizer.size(
        entry_price=50.0,
        stop_loss=45.0,
        avg_daily_volume=10_000.0,
        confidence=1.0,
    )
    assert res["quantity"] == 500
    assert res["position_value"] == 25_000.0
    assert res["position_size_pct"] == 0.025


def test_position_sizer_invalid_inputs():
    """Verify position sizing safely returns 0 for invalid prices."""
    sizer = PositionSizer()
    res1 = sizer.size(entry_price=0.0, stop_loss=10.0, avg_daily_volume=5000.0)
    assert res1["quantity"] == 0
    assert res1["position_size_pct"] == 0.0

    res2 = sizer.size(entry_price=50.0, stop_loss=55.0, avg_daily_volume=5000.0)
    assert res2["quantity"] == 0


def test_cost_aware_backtester_deducts_fees():
    """Verify CostAwareBacktester accounts for transaction fees."""
    backtester = CostAwareBacktester(initial_capital=100_000.0)
    # Commission + SEC + CSE levies
    expected_one_way = 0.0115 + 0.0015 + 0.0004
    assert round(backtester.one_way_fee, 4) == round(expected_one_way, 4)
