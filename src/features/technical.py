"""Technical indicators library for quantitative feature generation."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_returns(prices: pd.Series, periods: list[int] = [1, 5, 10, 20]) -> pd.DataFrame:
    """Compute percentage returns over multiple trading horizons."""
    df = pd.DataFrame(index=prices.index)
    for p in periods:
        df[f"return_{p}d"] = prices.pct_change(p)
    return df


def compute_sma(prices: pd.Series, windows: list[int] = [5, 10, 20, 50, 100]) -> pd.DataFrame:
    """Compute Simple Moving Averages.

    Uses min_periods equal to the window size so that early warm-up rows
    with fewer observations than the window are left as NaN rather than
    being filled with a spurious partial average.
    """
    df = pd.DataFrame(index=prices.index)
    for w in windows:
        df[f"sma_{w}"] = prices.rolling(window=w, min_periods=w).mean()
    return df


def compute_ema(prices: pd.Series, spans: list[int] = [12, 26]) -> pd.DataFrame:
    """Compute Exponential Moving Averages."""
    df = pd.DataFrame(index=prices.index)
    for s in spans:
        df[f"ema_{s}"] = prices.ewm(span=s, adjust=False).mean()
    return df


def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index (RSI).

    Warm-up rows (fewer than `period` observations) are left as NaN.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

    # When all changes are gains (loss == 0), RSI is 100.0
    rsi = rsi.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)
    # When all changes are losses (gain == 0), RSI is 0.0
    rsi = rsi.where(~((avg_gain == 0) & (avg_loss > 0)), 0.0)
    # Warm-up rows stay NaN — do NOT fill with a fake neutral value.
    return rsi


def compute_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Compute Moving Average Convergence Divergence (MACD)."""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line

    return pd.DataFrame(
        {"macd": macd_line, "macd_signal": signal_line, "macd_histogram": hist},
        index=prices.index,
    )


def compute_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Compute Stochastic Oscillator %K and %D.

    Warm-up rows (fewer than k_period bars) are left as NaN rather than
    being filled with a fake midpoint value of 50.
    """
    low_min = low.rolling(window=k_period, min_periods=k_period).min()
    high_max = high.rolling(window=k_period, min_periods=k_period).max()
    denom = (high_max - low_min).replace(0, np.nan)

    k = 100 * ((close - low_min) / denom)
    # Do NOT fillna(50): leave warm-up rows as NaN.
    d = k.rolling(window=d_period, min_periods=d_period).mean()

    return pd.DataFrame({"stochastic_k": k, "stochastic_d": d}, index=close.index)


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Average True Range (ATR)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr


def compute_bollinger_bands(prices: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Compute Bollinger Bands (upper, lower, bandwidth).

    Warm-up rows (fewer than `period` observations) are left as NaN.
    """
    sma = prices.rolling(window=period, min_periods=period).mean()
    std = prices.rolling(window=period, min_periods=period).std()

    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    width = (upper - lower) / sma.replace(0, np.nan)

    return pd.DataFrame(
        {"bollinger_upper": upper, "bollinger_lower": lower, "bollinger_width": width},
        index=prices.index,
    )


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Compute On-Balance Volume (OBV)."""
    direction = np.sign(close.diff()).fillna(0)
    obv = (direction * volume).cumsum()
    return obv


def compute_volatility(prices: pd.Series, period: int = 20) -> pd.Series:
    """Compute annualized rolling price volatility.

    Warm-up rows are left as NaN rather than filled with a fake zero.
    """
    ret = prices.pct_change()
    vol = ret.rolling(window=period, min_periods=period).std() * np.sqrt(252)
    return vol


def compute_52w_position(prices: pd.Series, window: int = 252) -> pd.DataFrame:
    """Compute relative distance from 52-week rolling high and low."""
    rolling_high = prices.rolling(window=window, min_periods=10).max()
    rolling_low = prices.rolling(window=window, min_periods=10).min()

    dist_high = (prices - rolling_high) / rolling_high.replace(0, np.nan)
    dist_low = (prices - rolling_low) / rolling_low.replace(0, np.nan)

    return pd.DataFrame(
        {"dist_from_52w_high": dist_high, "dist_from_52w_low": dist_low},
        index=prices.index,
    )
