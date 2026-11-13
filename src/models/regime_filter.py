"""Market regime filter based on ASPI trend and volatility conditions."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# TODO: compute from live ASPI data — the caller in decision.py currently passes
# a hardcoded volatility value (0.18) instead of a realised figure.
# Use classify_from_prices() wherever a price series is available to avoid
# HIGH_VOLATILITY never triggering when actual market turbulence is high.
_HARDCODED_VOL_SENTINEL = 0.18  # value passed by legacy callers


class RegimeFilter:
    """Classifies the market environment to guard against trading during bear or extreme volatility conditions."""

    def __init__(self, vol_threshold: float = 0.28):
        # vol_threshold: annualised ASPI volatility (σ × √252) above which the
        # regime is flagged HIGH_VOLATILITY.  Default 0.28 ≈ 28 % annualised.
        self.vol_threshold = vol_threshold

    def compute_realised_volatility(self, aspi_prices: list[float] | pd.Series, lookback: int = 20) -> float:
        """Compute annualised realised volatility from the most recent *lookback* ASPI closes.

        Args:
            aspi_prices: Sequence of ASPI close prices ordered oldest-first.
            lookback:    Number of recent trading days to use (default 20).

        Returns:
            Annualised volatility as a float, or ``self.vol_threshold`` as a
            safe default when insufficient data is available.
        """
        prices = pd.Series(aspi_prices, dtype=float) if not isinstance(aspi_prices, pd.Series) else aspi_prices.astype(float)
        recent = prices.iloc[-lookback:] if len(prices) >= lookback + 1 else prices
        returns = recent.pct_change().dropna()
        if len(returns) < 2:
            # Insufficient history — fall back to threshold so we neither over-
            # nor under-trigger the HIGH_VOLATILITY regime.
            logger.warning(
                "RegimeFilter: too few ASPI returns (%d) to estimate volatility; defaulting to vol_threshold %.3f",
                len(returns),
                self.vol_threshold,
            )
            return self.vol_threshold
        return float(np.std(returns) * np.sqrt(252))

    def classify_from_prices(
        self,
        aspi_prices: list[float] | pd.Series,
        lookback_vol: int = 20,
        lookback_sma: int = 100,
    ) -> dict[str, Any]:
        """Classify market regime directly from an ASPI price series.

        Computes both the 100-day SMA and the 20-day realised volatility from
        ``aspi_prices`` so callers do not need to pass a hardcoded volatility.

        Args:
            aspi_prices:  ASPI close prices ordered oldest-first.
            lookback_vol: Days used for realised volatility (default 20).
            lookback_sma: Days used for the SMA benchmark (default 100).

        Returns:
            Same dict as :meth:`classify`.
        """
        prices = pd.Series(aspi_prices, dtype=float) if not isinstance(aspi_prices, pd.Series) else aspi_prices.astype(float)
        curr_aspi = float(prices.iloc[-1])

        # SMA100 — if fewer than lookback_sma rows are available, mean of whatever
        # we have; this is an explicit approximation, not a silent NaN fallback.
        if len(prices) < lookback_sma:
            logger.warning(
                "RegimeFilter: only %d ASPI rows available for SMA%d — using mean of available rows as approximation.",
                len(prices),
                lookback_sma,
            )
        # TODO: compute from live ASPI data — extend the query to fetch ≥100 rows.
        aspi_sma100 = float(prices.mean()) if len(prices) < lookback_sma else float(prices.iloc[-lookback_sma:].mean())

        realised_vol = self.compute_realised_volatility(prices, lookback=lookback_vol)
        return self.classify(curr_aspi, aspi_sma100, realised_vol)

    def classify(self, aspi_close: float, aspi_sma100: float, aspi_volatility: float) -> dict[str, Any]:
        """Determine regime status.

        - BULLISH: ASPI > 100-day SMA and volatility < threshold
        - BEARISH: ASPI <= 100-day SMA
        - HIGH_VOLATILITY: volatility >= threshold
        """
        if aspi_volatility >= self.vol_threshold:
            regime = "HIGH_VOLATILITY"
            allow_buy = False
            scale = 0.5
        elif aspi_close >= aspi_sma100:
            regime = "BULLISH"
            allow_buy = True
            scale = 1.0
        else:
            regime = "BEARISH"
            allow_buy = False
            scale = 0.25

        return {
            "regime": regime,
            "allow_buy": allow_buy,
            "position_scale": scale,
            "aspi_close": aspi_close,
            "aspi_sma100": aspi_sma100,
            "aspi_volatility": aspi_volatility,
        }
