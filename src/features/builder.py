"""Feature Builder: assembles technical and regime indicators into features.feature_daily."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.features.fundamental import compute_liquidity_features, compute_relative_strength
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
from src.utils.time_utils import trading_date as get_trading_date

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """Computes all technical, liquidity, and regime features point-in-time."""

    def __init__(self, session: Session):
        self.session = session

    def fetch_price_series(self, security_id: int, as_of_date: date) -> pd.DataFrame:
        """Fetch historical prices for a security up to as_of_date."""
        query = text("""
            SELECT trading_date, open, high, low, close, volume, turnover, adj_close
            FROM core.fact_price_daily
            WHERE security_id = :sec_id
              AND trading_date <= :as_of
            ORDER BY trading_date ASC
        """)
        df = pd.read_sql(query, self.session.bind, params={"sec_id": security_id, "as_of": as_of_date})
        if not df.empty:
            df["trading_date"] = pd.to_datetime(df["trading_date"]).dt.date
            df.set_index("trading_date", inplace=True)
        return df

    def fetch_aspi_series(self, as_of_date: date) -> pd.DataFrame:
        """Fetch ASPI index history up to as_of_date."""
        query = text("""
            SELECT trading_date, close, change_pct
            FROM core.fact_index_daily
            WHERE index_name = 'ASPI'
              AND trading_date <= :as_of
            ORDER BY trading_date ASC
        """)
        df = pd.read_sql(query, self.session.bind, params={"as_of": as_of_date})
        if not df.empty:
            df["trading_date"] = pd.to_datetime(df["trading_date"]).dt.date
            df.set_index("trading_date", inplace=True)
        return df

    def compute_for_security(self, security_id: int, as_of_date: date) -> pd.DataFrame:
        """Generate complete feature row for a given security as of as_of_date."""
        df_price = self.fetch_price_series(security_id, as_of_date)
        if df_price.empty or len(df_price) < 2:
            return pd.DataFrame()

        close = df_price["close"].astype(float)
        volume = df_price["volume"].astype(float)
        turnover = df_price["turnover"].astype(float)

        if "adj_close" in df_price.columns:
            adjusted_close = pd.to_numeric(df_price["adj_close"], errors="coerce")
            price = adjusted_close.where(adjusted_close.gt(0), close)
        else:
            logger.warning(
                "adj_close not available for security_id=%s as_of=%s; "
                "falling back to unadjusted close for feature computation.",
                security_id,
                as_of_date,
            )
            price = close
        adjustment_factor = (price / close.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        adjustment_factor = adjustment_factor.fillna(1.0)
        high = df_price["high"].astype(float) * adjustment_factor
        low = df_price["low"].astype(float) * adjustment_factor

        # 1. Technical features
        ret_df = compute_returns(price)
        sma_df = compute_sma(price)
        ema_df = compute_ema(price)
        rsi_series = compute_rsi(price)
        macd_df = compute_macd(price)
        stoch_df = compute_stochastic(high, low, price)
        atr_series = compute_atr(high, low, price)
        bb_df = compute_bollinger_bands(price)
        vol_series = compute_volatility(price)
        obv_series = compute_obv(price, volume)
        pos_df = compute_52w_position(price)
        liq_df = compute_liquidity_features(volume, turnover)

        # 2. Benchmark & Regime features
        df_aspi = self.fetch_aspi_series(as_of_date)
        if not df_aspi.empty and len(df_aspi) > 1:
            aspi_close = df_aspi["close"].astype(float)
            aspi_ret = aspi_close.pct_change()
            rs_5d = (price.pct_change(5) - aspi_ret.rolling(5).sum()).fillna(0.0)
            rs_20d = (price.pct_change(20) - aspi_ret.rolling(20).sum()).fillna(0.0)
            aspi_sma100 = aspi_close.rolling(100, min_periods=10).mean()
            aspi_above_sma = aspi_close > aspi_sma100
            aspi_vol = aspi_ret.rolling(20, min_periods=2).std() * np.sqrt(252)
        else:
            rs_5d = pd.Series(0.0, index=close.index)
            rs_20d = pd.Series(0.0, index=close.index)
            aspi_above_sma = pd.Series(True, index=close.index)
            aspi_vol = pd.Series(0.15, index=close.index)

        features = pd.concat(
            [
                ret_df,
                sma_df,
                ema_df,
                macd_df,
                stoch_df,
                bb_df,
                pos_df,
                liq_df,
            ],
            axis=1,
        )
        features["rsi_14"] = rsi_series
        features["atr_14"] = atr_series
        features["volatility_20d"] = vol_series
        features["obv"] = obv_series
        features["rs_vs_aspi_5d"] = rs_5d
        features["rs_vs_aspi_20d"] = rs_20d
        features["rs_vs_sector_5d"] = rs_5d  # fallback
        features["rs_vs_sector_20d"] = rs_20d  # fallback
        features["aspi_above_sma100"] = aspi_above_sma
        features["aspi_volatility_20d"] = aspi_vol
        features["security_id"] = security_id
        features["as_of_date"] = features.index
        features["feature_version"] = 1

        return features

    def save_features(self, features_df: pd.DataFrame) -> int:
        """Upsert computed features dataframe into features.feature_daily."""
        if features_df.empty:
            return 0

        upsert_query = text("""
            INSERT INTO features.feature_daily (
                security_id, trading_date, feature_version,
                return_1d, return_5d, return_10d, return_20d,
                sma_5, sma_10, sma_20, sma_50, sma_100,
                ema_12, ema_26,
                rsi_14, macd, macd_signal, macd_histogram,
                stochastic_k, stochastic_d,
                atr_14, bollinger_upper, bollinger_lower, bollinger_width,
                volatility_20d,
                volume_sma_20, volume_ratio, obv,
                rs_vs_aspi_5d, rs_vs_aspi_20d, rs_vs_sector_5d, rs_vs_sector_20d,
                avg_daily_turnover_20d, avg_daily_volume_20d,
                dist_from_52w_high, dist_from_52w_low,
                aspi_above_sma100, aspi_volatility_20d,
                as_of_date, computed_at
            ) VALUES (
                :security_id, :trading_date, :feature_version,
                :return_1d, :return_5d, :return_10d, :return_20d,
                :sma_5, :sma_10, :sma_20, :sma_50, :sma_100,
                :ema_12, :ema_26,
                :rsi_14, :macd, :macd_signal, :macd_histogram,
                :stochastic_k, :stochastic_d,
                :atr_14, :bollinger_upper, :bollinger_lower, :bollinger_width,
                :volatility_20d,
                :volume_sma_20, :volume_ratio, :obv,
                :rs_vs_aspi_5d, :rs_vs_aspi_20d, :rs_vs_sector_5d, :rs_vs_sector_20d,
                :avg_daily_turnover_20d, :avg_daily_volume_20d,
                :dist_from_52w_high, :dist_from_52w_low,
                :aspi_above_sma100, :aspi_volatility_20d,
                :as_of_date, NOW()
            )
            ON CONFLICT (security_id, trading_date, feature_version) DO UPDATE SET
                return_1d = EXCLUDED.return_1d,
                return_5d = EXCLUDED.return_5d,
                return_10d = EXCLUDED.return_10d,
                return_20d = EXCLUDED.return_20d,
                sma_5 = EXCLUDED.sma_5,
                sma_10 = EXCLUDED.sma_10,
                sma_20 = EXCLUDED.sma_20,
                sma_50 = EXCLUDED.sma_50,
                sma_100 = EXCLUDED.sma_100,
                ema_12 = EXCLUDED.ema_12,
                ema_26 = EXCLUDED.ema_26,
                rsi_14 = EXCLUDED.rsi_14,
                macd = EXCLUDED.macd,
                macd_signal = EXCLUDED.macd_signal,
                macd_histogram = EXCLUDED.macd_histogram,
                stochastic_k = EXCLUDED.stochastic_k,
                stochastic_d = EXCLUDED.stochastic_d,
                atr_14 = EXCLUDED.atr_14,
                bollinger_upper = EXCLUDED.bollinger_upper,
                bollinger_lower = EXCLUDED.bollinger_lower,
                bollinger_width = EXCLUDED.bollinger_width,
                volatility_20d = EXCLUDED.volatility_20d,
                volume_sma_20 = EXCLUDED.volume_sma_20,
                volume_ratio = EXCLUDED.volume_ratio,
                obv = EXCLUDED.obv,
                rs_vs_aspi_5d = EXCLUDED.rs_vs_aspi_5d,
                rs_vs_aspi_20d = EXCLUDED.rs_vs_aspi_20d,
                rs_vs_sector_5d = EXCLUDED.rs_vs_sector_5d,
                rs_vs_sector_20d = EXCLUDED.rs_vs_sector_20d,
                avg_daily_turnover_20d = EXCLUDED.avg_daily_turnover_20d,
                avg_daily_volume_20d = EXCLUDED.avg_daily_volume_20d,
                dist_from_52w_high = EXCLUDED.dist_from_52w_high,
                dist_from_52w_low = EXCLUDED.dist_from_52w_low,
                aspi_above_sma100 = EXCLUDED.aspi_above_sma100,
                aspi_volatility_20d = EXCLUDED.aspi_volatility_20d,
                as_of_date = EXCLUDED.as_of_date,
                computed_at = NOW()
        """)

        rows = []
        for dt_idx, row in features_df.iterrows():
            params = row.to_dict()
            params["trading_date"] = dt_idx
            # Replace NaNs with None for SQL NULL
            clean_params = {k: (None if pd.isna(v) else v) for k, v in params.items()}
            rows.append(clean_params)

        if rows:
            self.session.execute(upsert_query, rows)
            self.session.commit()
        return len(rows)

    def build_all_features(self, target_date: date | None = None, historical: bool = False) -> int:
        """Build features for all active securities as of target date.

        Args:
            target_date: Date to compute features for (defaults to today's trading date).
            historical: If True, delegates to build_all_features_historical() to compute
                        features for every trading date in the price history.
        """
        if historical:
            return self.build_all_features_historical()

        t_date = target_date or get_trading_date()
        logger.info("Computing features for all active securities as of %s...", t_date)

        query = text("SELECT security_id, symbol FROM core.dim_security WHERE is_active = TRUE")
        securities = self.session.execute(query).fetchall()

        total_saved = 0
        for sec_id, _ in securities:
            feats = self.compute_for_security(sec_id, t_date)
            if not feats.empty:
                # Save the latest row only (point-in-time for today)
                saved = self.save_features(feats.tail(1))
                total_saved += saved

        logger.info("Features built for %d securities as of %s", total_saved, t_date)
        return total_saved

    def build_all_features_historical(
        self,
        security_ids: list[int] | None = None,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> int:
        """Build features for ALL trading dates across ALL active securities.

        Iterates every distinct trading date present in core.fact_price_daily for each
        security (point-in-time safe — only uses price history up to that date) and
        saves a single feature row per security/date.

        Returns:
            Total number of feature rows saved.
        """
        if security_ids is None:
            sec_query = text(
                "SELECT security_id, symbol FROM core.dim_security WHERE is_active = TRUE"
            )
            securities = self.session.execute(sec_query).fetchall()
        elif not security_ids:
            securities = []
        else:
            sec_query = text(
                "SELECT security_id, symbol FROM core.dim_security "
                "WHERE is_active = TRUE AND security_id = ANY(:security_ids)"
            )
            securities = self.session.execute(
                sec_query,
                {"security_ids": security_ids},
            ).fetchall()

        logger.info("Starting HISTORICAL feature build for %d active securities...", len(securities))
        total_saved = 0
        max_date_query = text(
            "SELECT MAX(trading_date) FROM core.fact_price_daily WHERE security_id = :sid"
        )
        for idx, (sec_id, _) in enumerate(securities):
            if idx % 10 == 0:
                logger.info(
                    "Historical features progress: %d / %d securities processed, %d rows saved so far",
                    idx,
                    len(securities),
                    total_saved,
                )
            latest_date = self.session.execute(max_date_query, {"sid": sec_id}).scalar()
            if latest_date is not None:
                feats = self.compute_for_security(sec_id, latest_date)
                total_saved += self.save_features(feats)
            if progress_callback:
                progress_callback(idx + 1, len(securities), total_saved)

        self.session.commit()
        logger.info("Historical feature build complete: %d total rows saved.", total_saved)
        return total_saved

    def build_features_for_security(self, security_id: int) -> int:
        """Build historical features for a single security across all its trading dates."""
        dates_query = text(
            "SELECT DISTINCT trading_date FROM core.fact_price_daily "
            "WHERE security_id = :sid ORDER BY trading_date"
        )
        dates = [r[0] for r in self.session.execute(dates_query, {"sid": security_id}).fetchall()]
        saved = 0
        for dt in dates:
            feats = self.compute_for_security(security_id, dt)
            if not feats.empty:
                saved += self.save_features(feats.tail(1))
        return saved
