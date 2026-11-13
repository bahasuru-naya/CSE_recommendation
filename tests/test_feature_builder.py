import numpy as np
import pandas as pd

from src.features.builder import FeatureBuilder


def test_price_features_use_consistent_adjusted_ohlc():
    sessions = pd.bdate_range("2025-01-01", periods=30)
    close = pd.Series(100.0 + np.arange(len(sessions)), index=sessions)
    prices = pd.DataFrame(
        {
            "open": close,
            "high": close + 2.0,
            "low": close - 2.0,
            "close": close,
            "adj_close": close * 0.5,
            "volume": 10_000.0,
            "turnover": 1_000_000.0,
        },
        index=sessions,
    )
    aspi = pd.DataFrame(
        {"close": 20_000.0 + np.arange(len(sessions))},
        index=sessions,
    )
    prices.index = sessions.date
    aspi.index = sessions.date
    builder = FeatureBuilder(session=None)
    builder.fetch_price_series = lambda security_id, as_of_date: prices
    builder.fetch_aspi_series = lambda as_of_date: aspi

    features = builder.compute_for_security(1, sessions[-1].date())

    assert features.iloc[-1]["sma_5"] == np.mean((close * 0.5).iloc[-5:])
    assert features.iloc[-1]["atr_14"] == 2.0
    assert features.iloc[-1]["as_of_date"] == sessions[-1].date()


def test_historical_feature_build_with_no_downloaded_securities_is_empty():
    class SessionStub:
        def __init__(self):
            self.committed = False

        def commit(self):
            self.committed = True

    session = SessionStub()
    builder = FeatureBuilder(session=session)

    assert builder.build_all_features_historical(security_ids=[]) == 0
    assert session.committed
