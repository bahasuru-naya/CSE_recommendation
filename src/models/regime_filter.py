"""Market regime filter based on ASPI trend and volatility conditions."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class RegimeFilter:
    """Classifies the market environment to guard against trading during bear or extreme volatility conditions."""

    def __init__(self, vol_threshold: float = 0.28):
        self.vol_threshold = vol_threshold

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
