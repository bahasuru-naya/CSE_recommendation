"""Tests for Technical Indicators and Feature Engineering Calculations."""

import numpy as np
import pandas as pd
import pytest

from src.features.technical import (
    compute_52w_position,
    compute_atr,
    compute_bollinger_bands,
    compute_ema,
    compute_macd,
    compute_obv,
    compute_returns,
    compute_rsi,
    compute_sma,
    compute_stochastic,
    compute_volatility,
)


@pytest.fixture
def sample_ohlcv():
    """Create 50 days of realistic synthetic price and volume data."""
    dates = pd.date_range("2026-01-01", periods=50, freq="B")
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.normal(0.5, 2.0, 50))
    high = close + np.random.uniform(0.5, 3.0, 50)
    low = close - np.random.uniform(0.5, 3.0, 50)
    volume = np.random.uniform(10_000, 100_000, 50)
    return pd.DataFrame({"close": close, "high": high, "low": low, "volume": volume}, index=dates)


def test_compute_returns(sample_ohlcv):
    """Verify returns calculation matches expected horizons."""
    df_ret = compute_returns(sample_ohlcv["close"], [1, 5])
    assert "return_1d" in df_ret.columns
    assert "return_5d" in df_ret.columns

    # First value of 1d return is NaN
    assert np.isnan(df_ret["return_1d"].iloc[0])
    # Second value matches (P1 - P0) / P0
    expected_ret = (sample_ohlcv["close"].iloc[1] - sample_ohlcv["close"].iloc[0]) / sample_ohlcv["close"].iloc[0]
    np.testing.assert_almost_equal(df_ret["return_1d"].iloc[1], expected_ret)


def test_compute_sma_and_ema(sample_ohlcv):
    """Verify SMA and EMA calculations are sensible."""
    sma = compute_sma(sample_ohlcv["close"], [5, 20])
    ema = compute_ema(sample_ohlcv["close"], [12, 26])

    assert "sma_5" in sma.columns
    assert "sma_20" in sma.columns
    assert "ema_12" in ema.columns
    assert "ema_26" in ema.columns

    # Mean of first 5 values matches sma_5 at index 4
    expected_sma5 = sample_ohlcv["close"].iloc[:5].mean()
    np.testing.assert_almost_equal(sma["sma_5"].iloc[4], expected_sma5)


def test_compute_rsi_bounds(sample_ohlcv):
    """Verify RSI values are strictly bounded within [0, 100]."""
    rsi = compute_rsi(sample_ohlcv["close"], period=14)
    assert np.all(rsi >= 0.0)
    assert np.all(rsi <= 100.0)

    # Monotonically increasing prices should have RSI close to 100
    up_prices = pd.Series([10.0 + i for i in range(30)])
    up_rsi = compute_rsi(up_prices, period=14)
    assert up_rsi.iloc[-1] > 90.0

    # Monotonically decreasing prices should have RSI close to 0
    down_prices = pd.Series([100.0 - i for i in range(30)])
    down_rsi = compute_rsi(down_prices, period=14)
    assert down_rsi.iloc[-1] < 10.0


def test_compute_macd_consistency(sample_ohlcv):
    """Verify MACD histogram equals macd_line - signal_line."""
    macd_df = compute_macd(sample_ohlcv["close"])
    assert "macd" in macd_df.columns
    assert "macd_signal" in macd_df.columns
    assert "macd_histogram" in macd_df.columns

    diff = macd_df["macd"] - macd_df["macd_signal"]
    np.testing.assert_allclose(macd_df["macd_histogram"], diff, rtol=1e-5)


def test_compute_atr_positive(sample_ohlcv):
    """Verify ATR is always non-negative."""
    atr = compute_atr(sample_ohlcv["high"], sample_ohlcv["low"], sample_ohlcv["close"], period=14)
    assert np.all(atr > 0.0)


def test_compute_bollinger_bands(sample_ohlcv):
    """Verify upper band >= lower band and width is non-negative."""
    bb = compute_bollinger_bands(sample_ohlcv["close"], period=20)
    assert np.all(bb["bollinger_upper"] >= bb["bollinger_lower"])
    assert np.all(bb["bollinger_width"] >= 0.0)


def test_compute_obv_and_volatility(sample_ohlcv):
    """Verify OBV and volatility compute without errors."""
    obv = compute_obv(sample_ohlcv["close"], sample_ohlcv["volume"])
    vol = compute_volatility(sample_ohlcv["close"], period=20)

    assert len(obv) == len(sample_ohlcv)
    assert np.all(vol >= 0.0)
