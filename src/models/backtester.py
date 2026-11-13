"""Cost-aware event simulation backtester for CSE trading strategies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
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
        eval_start_date: date | None = None,
        stop_pct: float | None = None,
        target_pct: float | None = None,
    ) -> tuple[BacktestMetrics, pd.DataFrame]:
        """Simulate next-session fills and mark the portfolio after all daily activity."""
        if prices.empty:
            raise ValueError("Price history is required for a backtest.")
        required_price_columns = {"trading_date", "symbol", "close"}
        missing = required_price_columns - set(prices.columns)
        if missing:
            raise ValueError(f"Price history is missing required columns: {', '.join(sorted(missing))}.")

        price_rows = prices.copy()
        signal_rows = signals.copy()
        price_rows["trading_date"] = pd.to_datetime(price_rows["trading_date"]).dt.normalize()
        if not signal_rows.empty:
            signal_rows["trading_date"] = pd.to_datetime(signal_rows["trading_date"]).dt.normalize()
        start_date = pd.Timestamp(eval_start_date).normalize() if eval_start_date is not None else None
        all_dates = pd.DatetimeIndex(price_rows["trading_date"].dropna().unique()).sort_values()
        date_to_next = dict(zip(all_dates[:-1], all_dates[1:], strict=True))
        pending_orders: dict[pd.Timestamp, list[dict[str, Any]]] = {}
        positions: dict[str, dict[str, Any]] = {}
        capital = self.initial_capital
        history: list[dict[str, Any]] = []
        closed_trades: list[dict[str, Any]] = []

        def close_position(symbol: str, position: dict[str, Any], when: pd.Timestamp, price: float) -> None:
            nonlocal capital
            net_proceeds = position["quantity"] * price * (1.0 - self.one_way_fee)
            capital += net_proceeds
            pnl = net_proceeds - position["quantity"] * position["entry_price"] * (1.0 + self.one_way_fee)
            closed_trades.append({
                "symbol": symbol,
                "entry_date": position["entry_date"],
                "exit_date": when,
                "pnl": pnl,
                "is_win": pnl > 0,
            })

        for current_date in all_dates:
            daily_prices = price_rows.loc[price_rows["trading_date"] == current_date].set_index("symbol")

            for order in pending_orders.pop(current_date, []):
                symbol = order["symbol"]
                if symbol not in daily_prices.index:
                    continue
                price_row = daily_prices.loc[symbol]
                open_price = price_row.get("open")
                fill_price = (
                    float(open_price)
                    if open_price is not None and pd.notna(open_price) and float(open_price) > 0
                    else float(price_row["close"])
                )
                if fill_price <= 0:
                    continue
                if order["signal"] == "SELL":
                    position = positions.pop(symbol, None)
                    if position is not None:
                        close_position(symbol, position, current_date, fill_price)
                    continue
                if order["signal"] != "BUY" or symbol in positions:
                    continue

                portfolio_value = capital + sum(
                    position["quantity"] * position["current_price"]
                    for position in positions.values()
                )
                allocation = portfolio_value * order["position_size_pct"]
                quantity = int(min(allocation, capital / (1.0 + self.one_way_fee)) / fill_price)
                if quantity <= 0:
                    continue
                capital -= quantity * fill_price * (1.0 + self.one_way_fee)
                position_stop_pct = order.get("stop_pct", stop_pct if stop_pct is not None else 0.08)
                position_target_pct = order.get("target_pct", target_pct if target_pct is not None else 0.15)
                positions[symbol] = {
                    "symbol": symbol,
                    "entry_date": current_date,
                    "entry_price": fill_price,
                    "quantity": quantity,
                    "current_price": fill_price,
                    "stop_loss": fill_price * (1.0 - position_stop_pct),
                    "target": fill_price * (1.0 + position_target_pct),
                }

            for symbol, position in list(positions.items()):
                if symbol not in daily_prices.index:
                    continue
                price_row = daily_prices.loc[symbol]
                close_price = float(price_row["close"])
                high_price = float(price_row["high"]) if "high" in price_row and pd.notna(price_row["high"]) else close_price
                low_price = float(price_row["low"]) if "low" in price_row and pd.notna(price_row["low"]) else close_price
                open_price = float(price_row["open"]) if "open" in price_row and pd.notna(price_row["open"]) else close_price
                position["current_price"] = close_price

                exit_price = None
                if open_price <= position["stop_loss"] or open_price >= position["target"]:
                    exit_price = open_price
                elif low_price <= position["stop_loss"]:
                    exit_price = position["stop_loss"]
                elif high_price >= position["target"]:
                    exit_price = position["target"]
                if exit_price is not None:
                    closed_position = positions.pop(symbol)
                    close_position(symbol, closed_position, current_date, exit_price)

            portfolio_value = capital
            for symbol, position in positions.items():
                if symbol in daily_prices.index:
                    position["current_price"] = float(daily_prices.loc[symbol, "close"])
                portfolio_value += position["quantity"] * position["current_price"]
            history.append({"trading_date": current_date, "portfolio_value": portfolio_value})

            if start_date is not None and current_date < start_date:
                continue
            next_date = date_to_next.get(current_date)
            if next_date is None or signal_rows.empty:
                continue
            day_signals = signal_rows.loc[signal_rows["trading_date"] == current_date]
            for _, signal in day_signals.drop_duplicates("symbol", keep="last").iterrows():
                action = signal["signal"]
                if action not in {"BUY", "SELL"}:
                    continue
                if action == "BUY":
                    allocation_pct = float(signal.get("position_size_pct", 0.10))
                    if allocation_pct <= 0:
                        continue
                    allocation_pct = min(allocation_pct, 1.0)
                else:
                    allocation_pct = 0.0
                pending_orders.setdefault(next_date, []).append({
                    "symbol": signal["symbol"],
                    "signal": action,
                    "position_size_pct": allocation_pct,
                    "stop_pct": float(signal.get("stop_pct", stop_pct if stop_pct is not None else 0.08)),
                    "target_pct": float(signal.get("target_pct", target_pct if target_pct is not None else 0.15)),
                })

        df_hist = pd.DataFrame(history)
        if df_hist.empty:
            raise ValueError("No price dates were available to calculate backtest metrics.")
        evaluation_history = (
            df_hist.loc[df_hist["trading_date"] >= start_date].copy()
            if start_date is not None
            else df_hist.copy()
        )
        if evaluation_history.empty:
            raise ValueError("No price dates fall within the requested evaluation window.")

        final_value = float(evaluation_history.iloc[-1]["portfolio_value"])
        total_return = final_value / self.initial_capital - 1.0
        evaluation_history["daily_return"] = evaluation_history["portfolio_value"].pct_change().fillna(0.0)
        daily_std = evaluation_history["daily_return"].std()
        sharpe = (
            evaluation_history["daily_return"].mean() / daily_std * np.sqrt(252)
            if pd.notna(daily_std) and daily_std > 0
            else 0.0
        )
        drawdown = (
            evaluation_history["portfolio_value"]
            / evaluation_history["portfolio_value"].cummax()
            - 1.0
        )
        max_drawdown = abs(float(drawdown.min()))
        evaluation_dates = len(evaluation_history)
        annualized_return = (
            ((final_value / self.initial_capital) ** (252 / evaluation_dates) - 1.0) * 100
            if final_value > 0 and evaluation_dates > 0
            else -100.0
        )
        benchmark_return = 0.0
        if benchmark_returns is not None and not benchmark_returns.empty:
            benchmark = benchmark_returns.copy()
            if isinstance(benchmark.index, pd.DatetimeIndex) or any(
                isinstance(value, (date, pd.Timestamp, np.datetime64)) for value in benchmark.index
            ):
                benchmark.index = pd.to_datetime(benchmark.index).normalize()
            elif len(benchmark) == len(all_dates):
                benchmark.index = all_dates
            else:
                raise ValueError("Benchmark returns must be indexed by trading date.")
            if start_date is not None:
                benchmark = benchmark.loc[benchmark.index >= start_date]
            benchmark_values = pd.to_numeric(benchmark, errors="coerce").dropna().to_numpy()
            if len(benchmark_values):
                benchmark_return = float(np.prod(1.0 + benchmark_values) - 1.0)

        evaluation_dates_set = set(evaluation_history["trading_date"])
        evaluation_trades = [
            trade for trade in closed_trades
            if trade["exit_date"] in evaluation_dates_set
        ]
        win_rate = (
            sum(trade["is_win"] for trade in evaluation_trades) / len(evaluation_trades)
            if evaluation_trades
            else 0.0
        )
        metrics = BacktestMetrics(
            initial_capital=self.initial_capital,
            final_capital=final_value,
            total_return_pct=total_return * 100,
            annualized_return_pct=annualized_return,
            sharpe_ratio=round(float(sharpe), 2),
            max_drawdown_pct=round(max_drawdown * 100, 2),
            win_rate=round(win_rate * 100, 1),
            total_trades=len(evaluation_trades),
            benchmark_return_pct=round(benchmark_return * 100, 2),
            excess_return_pct=round((total_return - benchmark_return) * 100, 2),
        )
        return metrics, evaluation_history.reset_index(drop=True)
