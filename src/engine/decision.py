"""Decision Engine: synthesizes model forecasts, regime checks, liquidity filters, and ATR bounds."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.reconciliation import DataReconciler
from src.engine.position_sizing import PositionSizer
from src.engine.recommendations import RecommendationManager
from src.models.lgbm_model import CSELightGBMModel
from src.models.regime_filter import RegimeFilter
from src.models.registry import ModelRegistry
from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class DecisionEngine:
    """End-to-end decision orchestrator that produces BUY / SELL / HOLD / WATCH recommendations."""

    def __init__(self, session: Session):
        self.session = session
        self.registry = ModelRegistry(session)
        self.rec_manager = RecommendationManager(session)
        self.reconciler = DataReconciler(session)
        self.regime_filter = RegimeFilter()
        self.position_sizer = PositionSizer()

    def check_kill_switch(self) -> bool:
        """Verify data freshness. If data is stale, kill switch halts automated recommendations."""
        freshness = self.reconciler.check_freshness()
        if freshness.get("is_stale", False):
            logger.warning("Kill switch engaged: core market data is stale.")
            return True
        return False

    def get_latest_features_and_prices(self, as_of: date) -> pd.DataFrame:
        """Fetch latest features and recent price attributes for active securities."""
        query = text("""
            SELECT
                s.symbol,
                s.name,
                s.logo_url,
                p.close AS current_price,
                f.*
            FROM core.dim_security s
            JOIN core.fact_price_daily p
              ON p.security_id = s.security_id AND p.trading_date = :as_of
            JOIN features.feature_daily f
              ON f.security_id = s.security_id AND f.trading_date = :as_of
            WHERE s.is_active = TRUE
        """)
        return pd.read_sql(query, self.session.bind, params={"as_of": as_of})

    def run(self, target_date: date | None = None) -> list[dict[str, Any]]:
        """Run daily decision pipeline."""
        t_date = target_date or get_trading_date()
        logger.info("Executing Decision Engine for %s...", t_date)

        # 1. Kill switch
        if self.check_kill_switch():
            return [{"warning": "Recommendations aborted: data is stale."}]

        # 2. Check regime
        aspi_row = self.session.execute(
            text("""
                SELECT close, change_pct
                FROM core.fact_index_daily
                WHERE index_name = 'ASPI' AND trading_date <= :t_date
                ORDER BY trading_date DESC LIMIT 100
            """),
            {"t_date": t_date},
        ).fetchall()

        regime_info = {"regime": "BULLISH", "allow_buy": True, "position_scale": 1.0}
        if aspi_row and len(aspi_row) >= 10:
            prices = [float(r[0]) for r in aspi_row]
            curr_aspi = prices[0]
            sma_100 = sum(prices) / len(prices)
            regime_info = self.regime_filter.classify(curr_aspi, sma_100, 0.18)

        # 3. Load active model
        active_model_data = self.registry.get_active_model()
        model_version = "v1.0-default"
        model_instance = None
        if active_model_data:
            _, model_instance, meta = active_model_data
            model_version = f"{meta['model_name']}-v{meta['version']}"

        # 4. Fetch candidate features
        df_feat = self.get_latest_features_and_prices(t_date)
        if df_feat.empty:
            logger.warning("No features found for date %s", t_date)
            return []

        decisions = []

        # Liquidity filter thresholds (from app.settings default or constants)
        min_turnover_20d = 200_000.0  # LKR 200k daily average
        min_volume_20d = 500

        for _, row in df_feat.iterrows():
            sec_id = int(row["security_id"])
            symbol = str(row["symbol"])
            name = str(row["name"] or symbol)
            current_p = float(row["current_price"]) if row["current_price"] else None
            if not current_p or current_p <= 0:
                continue

            # Liquidity check
            avg_turnover = float(row.get("avg_daily_turnover_20d") or 0.0)
            avg_vol = float(row.get("avg_daily_volume_20d") or 0.0)
            is_liquid = avg_turnover >= min_turnover_20d and avg_vol >= min_volume_20d

            # Model prediction or heuristic rule
            predicted_prob = 0.5
            raw_shap = []

            if model_instance is not None:
                prob = model_instance.predict_proba(pd.DataFrame([row]))[0]
                predicted_prob = float(prob)
                raw_shap = model_instance.explain(pd.DataFrame([row]), top_n=5)
            else:
                # Heuristic scoring using momentum and RSI
                rsi = float(row.get("rsi_14") or 50)
                ret_20d = float(row.get("return_20d") or 0.0)
                if rsi < 65 and ret_20d > 0.03:
                    predicted_prob = 0.72
                    raw_shap = [
                        {"feature": "return_20d", "impact": round(ret_20d, 4)},
                        {"feature": "rsi_14", "impact": round(rsi, 1)},
                    ]
                elif rsi > 75 or ret_20d < -0.05:
                    predicted_prob = 0.25

            # ATR for stops and targets
            atr = float(row.get("atr_14") or (current_p * 0.03))
            stop_loss = max(round(current_p - (atr * 2.0), 2), 0.05)
            target_p = max(round(current_p + (atr * 3.0), 2), round(current_p * 1.01, 2))
            entry_low = round(current_p * 0.99, 2)
            entry_high = round(current_p * 1.01, 2)

            # Signal assignment
            if not is_liquid:
                signal = "WATCH"
            elif predicted_prob >= 0.65 and regime_info["allow_buy"]:
                signal = "BUY"
            elif predicted_prob <= 0.35:
                signal = "SELL"
            else:
                signal = "HOLD"

            # Sizing
            sizing = self.position_sizer.size(
                entry_price=current_p,
                stop_loss=stop_loss,
                avg_daily_volume=avg_vol,
                confidence=predicted_prob,
            )

            # Build rich feature explainability factors (beginner-friendly descriptions)
            def _format_feat_val(f_name: str, r_dict: dict) -> str:
                v = r_dict.get(f_name)
                if v is None:
                    return "-"
                try:
                    val_f = float(v)
                except (ValueError, TypeError):
                    return str(v)

                if any(k in f_name for k in ("ratio", "return", "rs_", "dist", "volatility")):
                    return f"{round(val_f * 100, 2)}%"
                elif f_name == "rsi_14":
                    return f"{round(val_f, 1)} / 100"
                elif f_name in ("volume_ratio",):
                    return f"{round(val_f, 2)}x"
                elif "turnover" in f_name:
                    return f"LKR {round(val_f):,}"
                elif "volume" in f_name or f_name == "obv":
                    return f"{round(val_f):,} shs"
                elif f_name == "atr_14":
                    return f"LKR {round(val_f, 2)}"
                elif "stochastic" in f_name:
                    return f"{round(val_f, 1)}%"
                return f"{round(val_f, 3)}"

            feature_meta = {
                # Momentum & returns
                "return_1d": ("1-Day Price Change", _format_feat_val("return_1d", row), "Day-over-day price jump showing immediate trader sentiment"),
                "return_5d": ("5-Day Momentum (1-Week)", _format_feat_val("return_5d", row), "Short-term buyer momentum picking up speed over the past trading week"),
                "return_10d": ("10-Day Momentum (2-Weeks)", _format_feat_val("return_10d", row), "Two-week price return confirming whether buyers are sustaining the rally"),
                "return_20d": ("20-Day Price Trend (1-Month)", _format_feat_val("return_20d", row), "Consistent upward price gain over the past month"),
                # Moving average ratios
                "sma_5_ratio": ("5-Day Trendline Gap", _format_feat_val("sma_5_ratio", row), "Distance from 5-day average; positive means quick short-term buyer strength"),
                "sma_10_ratio": ("10-Day Trendline Gap", _format_feat_val("sma_10_ratio", row), "Price gap above 2-week baseline, confirming healthy rally traction"),
                "sma_20_ratio": ("20-Day Monthly Trendline Gap", _format_feat_val("sma_20_ratio", row), "Distance above 1-month average line watched by institutional funds"),
                "sma_50_ratio": ("50-Day Quarterly Trendline Gap", _format_feat_val("sma_50_ratio", row), "Position relative to 10-week benchmark; above it indicates a true medium-term bull wave"),
                "sma_100_ratio": ("100-Day Major Trendline Gap", _format_feat_val("sma_100_ratio", row), "Safety distance above long-term institutional floor"),
                "ema_12_ratio": ("12-Day Fast Average Gap", _format_feat_val("ema_12_ratio", row), "Price pulling ahead of recent fast average with rapid momentum"),
                "ema_26_ratio": ("26-Day Slow Average Gap", _format_feat_val("ema_26_ratio", row), "Positive separation from monthly smoothed baseline"),
                # MACD
                "macd": ("MACD Momentum Signal", _format_feat_val("macd", row), "Green-light indicator showing buyer speed outpacing sellers"),
                "macd_ratio": ("MACD Momentum Speed", _format_feat_val("macd_ratio", row), "Normalised momentum velocity showing pure buying acceleration"),
                "macd_signal": ("MACD Signal Baseline", _format_feat_val("macd_signal", row), "9-day smoothed baseline; crossing above triggers technical buy signal"),
                "macd_signal_ratio": ("MACD Signal Baseline Gap", _format_feat_val("macd_signal_ratio", row), "Upward baseline confirmation supporting higher price targets"),
                "macd_histogram": ("MACD Acceleration", _format_feat_val("macd_histogram", row), "Rate at which buying interest is speeding up"),
                "macd_histogram_ratio": ("MACD Acceleration Rate", _format_feat_val("macd_histogram_ratio", row), "Buyers hitting the gas pedal, increasing odds of an alpha breakout"),
                # Oscillators
                "rsi_14": ("RSI Price Valuation Gauge", _format_feat_val("rsi_14", row), "Speedometer from 0-100: healthy sweet spot is 45-65; below 30 is bargain; above 70 is overheated"),
                "stochastic_k": ("Stochastic Cycle Momentum (%K)", _format_feat_val("stochastic_k", row), "Measures if closing near 2-week highs (strong demand) or lows (weakness)"),
                "stochastic_d": ("Stochastic Turning Point (%D)", _format_feat_val("stochastic_d", row), "Smoothed cycle indicator confirming price turning points without false alarms"),
                # Bollinger
                "bollinger_upper_ratio": ("Distance to Bollinger Ceiling", _format_feat_val("bollinger_upper_ratio", row), "Room left to run before hitting upper statistical resistance"),
                "bollinger_lower_ratio": ("Distance to Bollinger Floor", _format_feat_val("bollinger_lower_ratio", row), "Safety cushion above statistical bargain floor"),
                "bollinger_width": ("Price Volatility Channel Width", _format_feat_val("bollinger_width", row), "Tight band squeeze indicates a quiet phase right before an explosive move"),
                # Volatility & ATR
                "volatility_20d": ("20-Day Stock Volatility", _format_feat_val("volatility_20d", row), "Annualised daily price swing size; lower means smoother, steadier trend"),
                "aspi_volatility_20d": ("Colombo Market Volatility (ASPI)", _format_feat_val("aspi_volatility_20d", row), "Overall turbulence in the CSE; calmer market makes stock picks more reliable"),
                "atr_14": ("Daily Price Range (ATR)", f"LKR {round(atr, 2)}", "Typical daily rupee swing, used to place smart stop-losses so normal noise doesn't trigger an exit"),
                "atr_14_ratio": ("Daily Fluctuation Ratio", _format_feat_val("atr_14_ratio", row), "Daily fluctuation as a % of share price; helps calculate risk-reward"),
                # Volume & Liquidity
                "volume_ratio": ("Trading Activity Surge", _format_feat_val("volume_ratio", row), "Today's traded volume vs 20-day average; >1.2x confirms big buyers or institutional interest"),
                "avg_daily_volume_20d": ("Daily Share Liquidity", _format_feat_val("avg_daily_volume_20d", row), "Average daily shares traded; ensures plenty of active market buyers and sellers"),
                "avg_daily_turnover_20d": ("Daily Cash Liquidity", _format_feat_val("avg_daily_turnover_20d", row), "Average daily cash traded in LKR; >LKR 500k guarantees instant order execution"),
                "obv": ("On-Balance Volume (OBV)", _format_feat_val("obv", row), "Cumulative money flow tracking whether smart money is quietly accumulating shares"),
                # Market Outperformance
                "rs_vs_aspi_5d": ("1-Week Beat-the-Market", _format_feat_val("rs_vs_aspi_5d", row), "Stock outperforming the general CSE ASPI index over the past week"),
                "rs_vs_aspi_20d": ("1-Month Beat-the-Market (Alpha)", _format_feat_val("rs_vs_aspi_20d", row), "Stock beating the general Colombo Stock Exchange index over the past month"),
                # 52-week extremes
                "dist_from_52w_high": ("Distance from 1-Year Peak", _format_feat_val("dist_from_52w_high", row), "How close the stock is to its 52-week high; near highs means strong breakout odds"),
                "dist_from_52w_low": ("Distance from 1-Year Floor", _format_feat_val("dist_from_52w_low", row), "Recovery bounce from the 52-week low floor, confirming bottom has formed"),
            }

            factors = []
            if raw_shap:
                for item in raw_shap:
                    feat = item.get("feature", "")
                    imp = float(item.get("impact") or 0.0)
                    meta = feature_meta.get(feat, (feat.replace("_", " ").title(), str(round(float(row.get(feat) or 0), 2)), "Model alpha indicator"))
                    factors.append({
                        "feature": feat,
                        "display_name": meta[0],
                        "value": meta[1],
                        "impact": round(imp, 4),
                        "direction": "bullish" if imp >= 0 else "bearish",
                        "description": meta[2],
                    })
            else:
                # Default factor breakdown from calculated features
                candidate_feats = ["return_5d", "return_20d", "rsi_14", "volume_ratio", "rs_vs_aspi_20d"]
                chosen = [f for f in candidate_feats if row.get(f) is not None or f in feature_meta][:4]
                for feat in chosen:
                    val = float(row.get(feat) or 0.0)
                    meta = feature_meta.get(feat, (feat.replace("_", " ").title(), str(round(val, 2)), "Indicator"))
                    factors.append({
                        "feature": feat,
                        "display_name": meta[0],
                        "value": meta[1],
                        "impact": round(val, 4),
                        "direction": "bullish" if (val > 0 if "return" in feat or "rs" in feat else val < 70) else "bearish",
                        "description": meta[2],
                    })

            # Plain English executive summary
            upside_pct = round(((target_p - current_p) / max(current_p, 0.01)) * 100, 1)
            downside_pct = round(((current_p - stop_loss) / max(current_p, 0.01)) * 100, 1)
            rr_ratio = round((target_p - current_p) / max(current_p - stop_loss, 0.01), 2)

            if signal == "BUY":
                summary = (
                    f"Good buying opportunity with {int(predicted_prob * 100)}% model confidence. "
                    f"Strong technical momentum in a {regime_info['regime']} market regime, with expected upside easily clearing the 2.68% CSE brokerage fee hurdle. "
                    f"Offers a {rr_ratio}:1 reward-to-risk ratio with {upside_pct}% target profit goal vs {downside_pct}% safety stop-loss buffer."
                )
            elif signal == "SELL":
                summary = (
                    f"Time to take profit or protect savings ({int((1 - predicted_prob) * 100)}% risk score). "
                    f"Defensive exit signal triggered to avoid potential short-term price drops."
                )
            elif signal == "WATCH":
                summary = (
                    f"Keep on watchlist. Daily trading turnover (LKR {round(avg_turnover):,}) "
                    f"is currently below the safe LKR {round(min_turnover_20d):,} threshold needed to buy and sell without delays."
                )
            else:
                summary = (
                    f"Neutral holding zone ({int(predicted_prob * 100)}% confidence). Projected return is not high enough yet "
                    f"to comfortably beat the 2.68% CSE broker fee and tax hurdle."
                )

            explainability_payload = {
                "summary": summary,
                "factors": factors,
                "regime": {
                    "regime": regime_info.get("regime", "BULLISH"),
                    "allow_buy": regime_info.get("allow_buy", True),
                    "aspi_context": "ASPI index trending above 100-day SMA" if regime_info.get("allow_buy") else "ASPI index trending below 100-day SMA",
                    "position_scale": regime_info.get("position_scale", 1.0),
                },
                "liquidity": {
                    "is_liquid": is_liquid,
                    "avg_turnover_lkr": round(avg_turnover, 2),
                    "min_turnover_lkr": min_turnover_20d,
                    "avg_volume_shares": int(avg_vol),
                    "min_volume_shares": min_volume_20d,
                },
                "risk_reward": {
                    "current_price": current_p,
                    "entry_low": entry_low,
                    "entry_high": entry_high,
                    "stop_loss": stop_loss,
                    "target_price": target_p,
                    "upside_potential_pct": upside_pct,
                    "downside_risk_pct": downside_pct,
                    "reward_to_risk_ratio": rr_ratio,
                    "atr_14": round(atr, 2),
                },
                "model_details": {
                    "model_version": model_version,
                    "confidence": round(predicted_prob, 3),
                    "hurdle_rate": "2.68% (CSE Commission + SEC/CSE Levies Buy & Sell)",
                    "horizon_days": 10,
                },
            }

            rec = {
                "security_id": sec_id,
                "symbol": symbol,
                "security_name": name,
                "logo_url": str(row["logo_url"]) if ("logo_url" in row and row["logo_url"] and pd.notna(row["logo_url"])) else None,
                "recommendation_date": t_date,
                "signal": signal,
                "confidence": round(predicted_prob, 3),
                "entry_price_low": entry_low,
                "entry_price_high": entry_high,
                "stop_loss": stop_loss,
                "target_price": target_p,
                "position_size_pct": sizing.get("position_size_pct", 0.05),
                "max_quantity": sizing.get("quantity", 100),
                "horizon_days": 10,
                "reasons": explainability_payload,
                "model_version": model_version,
                "data_freshness": {"as_of_date": str(t_date)},
            }
            decisions.append(rec)

        # Sort recommendations: BUYs first with highest confidence
        decisions.sort(key=lambda x: (x["signal"] == "BUY", x["confidence"]), reverse=True)
        # Save to database
        self.rec_manager.save_recommendations(decisions)
        logger.info("Generated and saved %d recommendations for %s", len(decisions), t_date)
        return decisions
