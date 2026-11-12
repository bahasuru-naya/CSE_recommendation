"""Tests for the CSE LightGBM AI Model and Explainability (SHAP).

Covers:
  - Training with the new normalised feature set (sma_N_ratio, ema_N_ratio, etc.)
  - Probability bounds, non-trivial predictions
  - Robustness to missing / extra columns
  - SHAP explainability
  - Serialisation round-trip
  - Target-creation hurdle-rate logic
"""

import numpy as np
import pandas as pd
import pytest

from src.models.lgbm_model import CSELightGBMModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_synthetic_X(n: int = 150, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame with the model's FEATURE_COLUMNS filled with plausible values.

    The model's _normalise_features() expects a 'price' column so it can compute ratios;
    we include it here, then verify it is NOT present in the trained model's feature list.
    """
    rng = np.random.default_rng(seed)
    data: dict[str, np.ndarray] = {}

    for col in CSELightGBMModel.FEATURE_COLUMNS:
        if "return" in col or "rs_" in col or "ratio" in col or "dist" in col:
            # Dimensionless ratios / percentage returns  (-0.3 … +0.3 typical)
            data[col] = rng.normal(0.0, 0.05, n)
        elif "rsi" in col or "stochastic" in col:
            data[col] = rng.uniform(20.0, 80.0, n)
        elif "volume" in col or "turnover" in col:
            data[col] = rng.uniform(1_000.0, 500_000.0, n)
        elif "volatility" in col:
            data[col] = rng.uniform(0.01, 0.40, n)
        elif "bollinger_width" in col:
            data[col] = rng.uniform(0.01, 0.15, n)
        else:
            data[col] = rng.normal(0.0, 1.0, n)

    # Include a 'price' column so _normalise_features() works (it will be dropped)
    data["price"] = rng.uniform(10.0, 300.0, n)

    return pd.DataFrame(data)


def _make_binary_label(n: int = 150, seed: int = 42) -> pd.Series:
    """Balanced-ish binary target so both classes appear in every split."""
    rng = np.random.default_rng(seed)
    # ~30% positive class (mimics real CSE imbalance but ensures ≥1 of each per fold)
    return pd.Series((rng.random(n) < 0.30).astype(int))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_feature_data():
    """200 synthetic observations with matching binary labels."""
    n = 200
    X = _make_synthetic_X(n=n)
    y = _make_binary_label(n=n)
    return X, y


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_ai_model_training_and_output_bounds(sample_feature_data):
    """Train the model; verify predict_proba returns values strictly in [0, 1]."""
    X, y = sample_feature_data
    split = 160
    X_train, y_train = X.iloc[:split], y.iloc[:split]
    X_val, y_val = X.iloc[split:], y.iloc[split:]

    # Use small n_estimators for speed; min_child_samples=5 to avoid leaf-size warnings
    model = CSELightGBMModel(params={"n_estimators": 50, "min_child_samples": 5})
    train_res = model.train(X_train, y_train, X_val, y_val)

    assert train_res["status"] == "trained", "train() must return status=trained"
    assert "feature_importance" in train_res
    assert isinstance(train_res["feature_importance"], dict)
    assert "scale_pos_weight" in train_res, "train() must report scale_pos_weight"

    preds = model.predict_proba(X_val)

    # Shape
    assert isinstance(preds, np.ndarray)
    assert len(preds) == len(X_val)

    # Probabilities bounded in [0, 1]
    assert np.all(preds >= 0.0), f"Prob < 0 found: {preds[preds < 0]}"
    assert np.all(preds <= 1.0), f"Prob > 1 found: {preds[preds > 1]}"

    # Not all constant (model learned something)
    assert not np.all(preds == preds[0]), "All predictions are identical – model did not learn"


def test_ai_model_price_column_not_leaked_into_features(sample_feature_data):
    """Ensure 'price' is used for normalisation but never passed to the booster."""
    X, y = sample_feature_data
    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 5})
    model.train(X, y)

    trained_features = model.model.feature_name()
    assert "price" not in trained_features, (
        "'price' column should be dropped by _normalise_features before training"
    )
    # Normalised ratio columns must be present
    assert "sma_5_ratio" in trained_features or "sma_10_ratio" in trained_features


def test_ai_model_normalised_features_replace_raw(sample_feature_data):
    """Normalised ratio columns are present; raw price-level columns are absent."""
    X, y = sample_feature_data
    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 5})
    model.train(X, y)

    trained_features = set(model.model.feature_name())
    # Raw columns that should have been normalised away
    for raw_col in CSELightGBMModel._PRICE_LEVEL_COLS:
        assert raw_col not in trained_features, (
            f"Raw price-level column '{raw_col}' should not be in trained feature set"
        )


def test_ai_model_single_observation_prediction(sample_feature_data):
    """Predict on a single row; verify scalar probability in [0, 1]."""
    X, y = sample_feature_data
    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 5})
    model.train(X, y)

    single_row = X.iloc[[0]]
    prob = model.predict_proba(single_row)

    assert len(prob) == 1
    assert 0.0 <= prob[0] <= 1.0


def test_ai_model_robustness_with_missing_and_extra_columns(sample_feature_data):
    """Model gracefully handles NaN values and extra irrelevant columns."""
    X, y = sample_feature_data
    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 5})
    model.train(X, y)

    corrupted_X = X.copy()
    corrupted_X["unrelated_column"] = "noisy_text"
    corrupted_X.loc[0:5, "return_1d"] = np.nan
    corrupted_X.loc[6:10, "rsi_14"] = np.nan

    preds = model.predict_proba(corrupted_X)
    assert len(preds) == len(X)
    assert not np.isnan(preds).any(), "NaN probabilities returned – fillna not working"
    assert np.all((preds >= 0.0) & (preds <= 1.0))


def test_ai_model_explainability_shap(sample_feature_data):
    """SHAP / feature importance explanation returns valid list of feature-impact pairs."""
    X, y = sample_feature_data
    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 5})
    model.train(X, y)

    single_row = X.iloc[[0]]
    explanations = model.explain(single_row, top_n=5)

    assert isinstance(explanations, list)
    assert 0 < len(explanations) <= 5

    for item in explanations:
        assert "feature" in item
        assert "impact" in item
        assert isinstance(item["feature"], str)
        assert isinstance(item["impact"], (float, int))
        assert not np.isnan(item["impact"]), "NaN impact value returned"


def test_ai_model_serialization(sample_feature_data):
    """Model serialises to bytes and restores with identical prediction output."""
    X, y = sample_feature_data
    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 5})
    model.train(X, y)

    orig_preds = model.predict_proba(X.iloc[:10])

    # Serialise
    model_bytes = model.to_bytes()
    assert isinstance(model_bytes, bytes)
    assert len(model_bytes) > 0

    # Deserialise
    restored_model = CSELightGBMModel.from_bytes(model_bytes)
    restored_preds = restored_model.predict_proba(X.iloc[:10])

    np.testing.assert_allclose(orig_preds, restored_preds, rtol=1e-5)


def test_ai_target_creation_with_hurdle_rate():
    """Forward-looking target properly applies 2.68% hurdle rate.

    stock[2] → stock[3]: +5% return, ASPI flat → excess = +5% > 2.68% → target=1
    stock[1] → stock[2]: 0% return, ASPI flat → excess = 0% < 2.68% → target=0
    """
    stock = pd.Series([100.0, 100.0, 100.0, 105.0])
    aspi = pd.Series([1000.0, 1000.0, 1000.0, 1000.0])

    target = CSELightGBMModel.create_target(
        stock_prices=stock,
        aspi_prices=aspi,
        horizon_days=1,
        round_trip_cost=0.0268,
    )

    # Row 2 (100→105 in 1 day): 5% > hurdle → 1
    assert target.iloc[2] == 1, f"Expected 1 got {target.iloc[2]}"
    # Row 1 (100→100 in 1 day): 0% < hurdle → 0
    assert target.iloc[1] == 0, f"Expected 0 got {target.iloc[1]}"


def test_ai_model_class_imbalance_handling():
    """scale_pos_weight is computed from actual label distribution, not hardcoded."""
    rng = np.random.default_rng(99)
    n = 200
    X = _make_synthetic_X(n=n, seed=99)
    # Very imbalanced: ~10% positive
    y = pd.Series((rng.random(n) < 0.10).astype(int))

    model = CSELightGBMModel(params={"n_estimators": 30, "min_child_samples": 2})
    result = model.train(X, y)

    spw = result.get("scale_pos_weight", 1.0)
    pos = result["train_pos"]
    neg = result["train_neg"]
    expected_spw = neg / pos if pos > 0 else 3.5
    assert abs(spw - expected_spw) < 0.1, (
        f"scale_pos_weight={spw:.2f} but expected ≈{expected_spw:.2f} "
        f"(pos={pos}, neg={neg})"
    )
