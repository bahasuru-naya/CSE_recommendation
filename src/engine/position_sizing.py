"""Position sizing and risk limit management."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PositionSizer:
    """Calculates quantity and capital allocation respecting liquidity and risk constraints."""

    def __init__(
        self,
        total_portfolio_value: float = 1_000_000.0,
        max_position_pct: float = 0.10,
        max_volume_pct: float = 0.05,
        risk_per_trade_pct: float = 0.02,
    ):
        self.portfolio_value = total_portfolio_value
        self.max_position_pct = max_position_pct
        self.max_volume_pct = max_volume_pct
        self.risk_per_trade_pct = risk_per_trade_pct

    def size(
        self,
        entry_price: float,
        stop_loss: float,
        avg_daily_volume: float,
        confidence: float = 0.70,
        position_scale: float = 1.0,
    ) -> dict[str, Any]:
        """Determine position quantity constrained by stop distance, portfolio cap, and average volume.

        Args:
            position_scale: Regime-driven multiplier (e.g. 0.5 during HIGH_VOLATILITY,
                            0.25 during BEARISH, 1.0 during BULLISH) applied after all
                            other constraints so the final quantity respects the market regime.
        """
        if entry_price <= 0 or stop_loss >= entry_price:
            return {"quantity": 0, "position_size_pct": 0.0, "reason": "Invalid entry or stop price"}

        # 1. Risk-based sizing: risk_amount = capital * risk_pct
        risk_amount = self.portfolio_value * self.risk_per_trade_pct * confidence
        risk_per_share = entry_price - stop_loss
        risk_qty = int(risk_amount / risk_per_share)

        # 2. Portfolio cap constraint (e.g. max 10% of portfolio in one stock)
        max_capital_for_pos = self.portfolio_value * self.max_position_pct
        cap_qty = int(max_capital_for_pos / entry_price)

        # 3. Liquidity constraint: max % of average daily volume
        liq_qty = int(avg_daily_volume * self.max_volume_pct) if avg_daily_volume > 0 else 1000

        # Choose conservative minimum, then apply regime position_scale
        raw_qty = max(0, min(risk_qty, cap_qty, liq_qty))
        final_qty = max(0, int(raw_qty * position_scale))
        position_value = final_qty * entry_price
        pos_pct = round(position_value / self.portfolio_value, 4)

        return {
            "quantity": final_qty,
            "position_size_pct": pos_pct,
            "position_value": position_value,
            "risk_qty": risk_qty,
            "cap_qty": cap_qty,
            "liq_qty": liq_qty,
            "position_scale": position_scale,
            "constrained_by": (
                "liquidity" if raw_qty == liq_qty else ("capital_cap" if raw_qty == cap_qty else "risk")
            ),
        }
