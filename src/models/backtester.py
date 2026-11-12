"""Cost-aware event simulation backtester for CSE trading strategies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    initial_capital: float
    final_capital: float
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    benchmark_return_pct: float
    excess_return_pct: float


class CostAwareBacktester:
    """Simulates portfolio performance deducting accurate CSE execution fees."""

    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        commission_pct: float = 0.0115,
        sec_levy_pct: float = 0.0015,
        cse_levy_pct: float = 0.0004,
    ):
        self.initial_capital = initial_capital
        # One-way transaction fee
        self.one_way_fee = commission_pct + sec_levy_pct + cse_levy_pct

    def run(
        self,
        signals: pd.DataFrame,
        prices: pd.DataFrame,
        benchmark_returns: pd.Series | None = None,
    ) -> tuple[BacktestMetrics, pd.DataFrame]:
        """Execute simulated backtest.

        signals: DataFrame with columns [trading_date, security_id, symbol, signal, confidence, position_size_pct]
        prices: DataFrame with columns [trading_date, security_id, open, close]
        """
        capital = self.initial_capital
        positions: dict[str, dict[str, Any]] = {}
        history = []
        closed_trades = []

        # Unique ordered trading dates
        all_dates = sorted(prices["trading_date"].unique())

        for current_date in all_dates:
            daily_prices = prices[prices["trading_date"] == current_date].set_index("symbol")

            # 1. Update valuation of existing positions
            portfolio_val = capital
            for sym, pos in list(positions.items()):
                if sym in daily_prices.index:
                    curr_p = float(daily_prices.loc[sym, "close"])
                    pos["current_price"] = curr_p
                    portfolio_val += pos["quantity"] * curr_p
                else:
                    portfolio_val += pos["quantity"] * pos["entry_price"]

            # 2. Check signals for today
            day_signals = signals[signals["trading_date"] == current_date]
            for _, sig in day_signals.iterrows():
                sym = sig["symbol"]
                action = sig["signal"]

                if action == "BUY" and sym not in positions and sym in daily_prices.index:
                    entry_p = float(daily_prices.loc[sym, "close"])
                    target_alloc = float(sig.get("position_size_pct", 0.10))
                    alloc_cash = portfolio_val * target_alloc
                    trade_cost = alloc_cash * (1.0 + self.one_way_fee)

                    if capital >= trade_cost and entry_p > 0:
                        qty = int(alloc_cash / entry_p)
                        if qty > 0:
                            actual_cost = qty * entry_p * (1.0 + self.one_way_fee)
                            capital -= actual_cost
                            positions[sym] = {
                                "symbol": sym,
                                "entry_date": current_date,
                                "entry_price": entry_p,
                                "quantity": qty,
                                "current_price": entry_p,
                                "stop_loss": entry_p * 0.92,
                                "target": entry_p * 1.15,
                            }

                elif action == "SELL" and sym in positions and sym in daily_prices.index:
                    pos = positions.pop(sym)
                    exit_p = float(daily_prices.loc[sym, "close"])
                    gross = pos["quantity"] * exit_p
                    net = gross * (1.0 - self.one_way_fee)
                    capital += net

                    pnl = net - (pos["quantity"] * pos["entry_price"] * (1.0 + self.one_way_fee))
                    closed_trades.append({
                        "symbol": sym,
                        "entry_date": pos["entry_date"],
                        "exit_date": current_date,
                        "pnl": pnl,
                        "is_win": pnl > 0,
                    })

            # Check stops & targets for remaining positions
            for sym, pos in list(positions.items()):
                if sym in daily_prices.index:
                    curr_p = float(daily_prices.loc[sym, "close"])
                    if curr_p <= pos["stop_loss"] or curr_p >= pos["target"]:
                        pos_closed = positions.pop(sym)
                        gross = pos_closed["quantity"] * curr_p
                        net = gross * (1.0 - self.one_way_fee)
                        capital += net
                        pnl = net - (pos_closed["quantity"] * pos_closed["entry_price"] * (1.0 + self.one_way_fee))
                        closed_trades.append({
                            "symbol": sym,
                            "entry_date": pos_closed["entry_date"],
                            "exit_date": current_date,
                            "pnl": pnl,
                            "is_win": pnl > 0,
                        })

            history.append({"trading_date": current_date, "portfolio_value": portfolio_val})

        df_hist = pd.DataFrame(history)
        if df_hist.empty:
            df_hist = pd.DataFrame([{"trading_date": date.today(), "portfolio_value": self.initial_capital}])

        # Calculate metrics
        final_val = df_hist.iloc[-1]["portfolio_value"]
        total_ret = (final_val - self.initial_capital) / self.initial_capital
        df_hist["daily_return"] = df_hist["portfolio_value"].pct_change().fillna(0)

        # Sharpe ratio
        std = df_hist["daily_return"].std()
        sharpe = (df_hist["daily_return"].mean() / std * np.sqrt(252)) if std > 0 else 0.0

        # Max drawdown
        cum_max = df_hist["portfolio_value"].cummax()
        drawdown = (df_hist["portfolio_value"] - cum_max) / cum_max
        max_dd = abs(drawdown.min())

        # Win rate
        win_count = sum(1 for t in closed_trades if t["is_win"])
        win_rate = (win_count / len(closed_trades)) if closed_trades else 0.0

        bench_ret = 0.0
        if benchmark_returns is not None and not benchmark_returns.empty:
            bench_ret = float(benchmark_returns.sum())

        metrics = BacktestMetrics(
            initial_capital=self.initial_capital,
            final_capital=final_val,
            total_return_pct=total_ret * 100,
            annualized_return_pct=total_ret * 100 * (252 / max(len(all_dates), 1)),
            sharpe_ratio=round(float(sharpe), 2),
            max_drawdown_pct=round(float(max_dd) * 100, 2),
            win_rate=round(win_rate * 100, 1),
            total_trades=len(closed_trades),
            benchmark_return_pct=round(bench_ret * 100, 2),
            excess_return_pct=round((total_ret - bench_ret) * 100, 2),
        )

        return metrics, df_hist
