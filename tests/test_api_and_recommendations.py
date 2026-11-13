"""End-to-End Tests for FastAPI Endpoints, Recommendations, and Portfolio Management."""

import json
from datetime import date

import pytest
from sqlalchemy import text
from starlette.testclient import TestClient

from src.api.main import app
from src.db import SessionLocal
from src.engine.recommendations import RecommendationManager


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture."""
    session = SessionLocal()
    yield session
    session.close()


# -----------------------------------------------------------------------------
# 1. System Health & Core API Tests
# -----------------------------------------------------------------------------

def test_health_check_endpoints(client):
    """Verify health endpoints respond with status: ok."""
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"
    assert res1.json()["service"] == "cse_recommendation_api"

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ok"


def test_settings_endpoints(client):
    """Verify settings listing and metadata."""
    res = client.get("/api/settings/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    # Must have standard system settings
    for key in ("liquidity_filter", "risk_limits", "model_config"):
        if key in data:
            assert "value" in data[key]
            assert "description" in data[key]


# -----------------------------------------------------------------------------
# 2. Recommendations Engine & Deduplication Tests
# -----------------------------------------------------------------------------

def test_recommendation_manager_deduplicates_test_batch_without_purging_newer_rows(db_session):
    """Verify duplicate test recommendations are deduplicated without deleting app data."""
    mgr = RecommendationManager(db_session)
    t_date = date(2000, 1, 1)

    # Create synthetic recommendations with intentional duplicate symbols
    batch = [
        {
            "security_id": 9999,
            "symbol": "DEDUP.N0000",
            "security_name": "Dedup Test",
            "signal": "BUY",
            "confidence": 0.68,
            "entry_price_low": 20.0,
            "entry_price_high": 21.0,
            "stop_loss": 18.0,
            "target_price": 25.0,
            "recommendation_date": t_date,
        },
        {
            "security_id": 9999,
            "symbol": "DEDUP.N0000",
            "security_name": "Dedup Test Higher Conf",
            "signal": "BUY",
            "confidence": 0.88,
            "entry_price_low": 20.0,
            "entry_price_high": 21.0,
            "stop_loss": 18.0,
            "target_price": 25.0,
            "recommendation_date": t_date,
        },
    ]

    saved = mgr.save_recommendations(batch)
    # Must save only 1 record (the higher confidence 0.88 one)
    assert saved == 1

    # Verify in DB
    rows = db_session.execute(
        text("SELECT symbol, confidence FROM app.recommendations WHERE symbol = 'DEDUP.N0000'")
    ).fetchall()
    assert len(rows) == 1
    assert round(float(rows[0][1]), 2) == 0.88

    # Cleanup test symbol
    db_session.execute(text("DELETE FROM app.recommendations WHERE symbol = 'DEDUP.N0000'"))
    db_session.commit()


def test_recommendation_manager_sanitizes_non_finite_json_values():
    class SessionStub:
        def __init__(self):
            self.insert_params = None
            self.committed = False
            self.rolled_back = False

        def execute(self, statement, params=None):
            if "INSERT INTO app.recommendations" in str(statement):
                self.insert_params = params

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    session = SessionStub()
    manager = RecommendationManager(session)
    saved = manager.save_recommendations([{
        "security_id": 1,
        "symbol": "NAN.N0000",
        "signal": "WATCH",
        "reasons": {"impact": float("nan"), "nested": [float("inf"), float("-inf")]},
    }])

    reasons = json.loads(session.insert_params["reasons"])
    assert saved == 1
    assert reasons == {"impact": None, "nested": [None, None]}
    assert session.committed
    assert not session.rolled_back


def test_recommendation_manager_rolls_back_and_surfaces_insert_errors():
    class SessionStub:
        def __init__(self):
            self.committed = False
            self.rolled_back = False

        def execute(self, statement, params=None):
            if "INSERT INTO app.recommendations" in str(statement):
                raise RuntimeError("insert failed")

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    session = SessionStub()
    manager = RecommendationManager(session)
    with pytest.raises(RuntimeError, match="insert failed"):
        manager.save_recommendations([{
            "security_id": 1,
            "symbol": "ERROR.N0000",
            "signal": "WATCH",
        }])

    assert not session.committed
    assert session.rolled_back


def test_get_recommendations_no_duplicates(client):
    """Verify GET /api/recommendations/ returns strictly unique stock symbols."""
    res = client.get("/api/recommendations/?signal=ALL&limit=100")
    assert res.status_code == 200
    payload = res.json()

    assert "total" in payload
    assert "data" in payload
    items = payload["data"]

    # Verify every symbol in the returned list is unique
    symbols = [r["symbol"].upper() for r in items]
    assert len(symbols) == len(set(symbols)), f"Duplicate symbols found: {symbols}"

    # Verify each recommendation structure
    for rec in items[:5]:
        assert "id" in rec
        assert "symbol" in rec
        assert rec["signal"] in ("BUY", "SELL", "HOLD", "WATCH")
        assert "has_open_position" in rec
        assert isinstance(rec["has_open_position"], bool)


def test_get_recommendations_by_signal(client):
    """Verify filtering recommendations by BUY signal."""
    res = client.get("/api/recommendations/?signal=BUY")
    assert res.status_code == 200
    payload = res.json()
    items = payload["data"]

    for rec in items:
        assert rec["signal"] == "BUY"
        assert rec["entry_price_low"] is not None or rec["entry_price_high"] is not None


def test_recommendation_execution_creates_open_position(client, db_session):
    """Verify executing a BUY recommendation opens an active position in portfolio."""
    test_sym = "EXECBUY.N0000"
    mgr = RecommendationManager(db_session)

    # Insert a temporary test recommendation
    batch = [{
        "security_id": 9876,
        "symbol": test_sym,
        "security_name": "Exec Buy Test",
        "signal": "BUY",
        "confidence": 0.82,
        "entry_price_low": 35.0,
        "entry_price_high": 36.0,
        "stop_loss": 32.0,
        "target_price": 42.0,
        "max_quantity": 250,
        "recommendation_date": date(2000, 1, 1),
    }]
    mgr.save_recommendations(batch)

    # Fetch created rec id
    rec_id = db_session.execute(
        text("SELECT id FROM app.recommendations WHERE symbol = :sym ORDER BY id DESC LIMIT 1"),
        {"sym": test_sym},
    ).scalar()
    assert rec_id is not None

    created_pos_id = None
    try:
        # Execute the recommendation
        res_exec = client.post(f"/api/recommendations/{rec_id}/execute")
        assert res_exec.status_code == 200
        data = res_exec.json()
        assert data["status"] == "success"
        assert data["new_status"] == "executed"
        assert "action" in data

        # Verify an open position was logged in app.portfolio_positions
        pos_row = db_session.execute(
            text("SELECT id, status, quantity, entry_price, stop_loss, target_price FROM app.portfolio_positions WHERE UPPER(symbol) = :sym AND status = 'open'"),
            {"sym": test_sym},
        ).fetchone()

        assert pos_row is not None
        created_pos_id = pos_row[0]
        assert pos_row[1] == "open"
        assert pos_row[2] == 250
        assert float(pos_row[3]) == 36.0
        assert float(pos_row[4]) == 32.0
        assert float(pos_row[5]) == 42.0

        # Verify recommendation details now show has_open_position = True
        res_detail = client.get(f"/api/recommendations/{rec_id}")
        assert res_detail.status_code == 200
        assert res_detail.json()["has_open_position"] is True

    finally:
        # Clean up
        if created_pos_id:
            db_session.execute(text("DELETE FROM app.portfolio_positions WHERE id = :id"), {"id": created_pos_id})
        db_session.execute(text("DELETE FROM app.recommendations WHERE symbol = :sym"), {"sym": test_sym})
        db_session.commit()


# -----------------------------------------------------------------------------
# 3. Portfolio Management & Lifecycle Tests
# -----------------------------------------------------------------------------

def test_portfolio_positions_lifecycle(client, db_session):
    """Full lifecycle: manual trade entry -> verify open -> close position -> permanent remove."""
    test_sym = "UNITTEST.N0000"

    # 1. Add manual open position
    add_payload = {
        "symbol": test_sym,
        "entry_price": 25.50,
        "quantity": 100,
        "stop_loss": 23.00,
        "target_price": 30.00,
        "notes": "Automated unit test position",
    }
    res_add = client.post("/api/portfolio/positions", json=add_payload)
    assert res_add.status_code == 200
    pos_id = res_add.json()["id"]
    assert pos_id > 0

    try:
        # 2. Check position appears in open positions
        res_list = client.get("/api/portfolio/positions?status=open")
        assert res_list.status_code == 200
        open_items = res_list.json()
        matching = [p for p in open_items if p["id"] == pos_id]
        assert len(matching) == 1
        assert matching[0]["symbol"] == test_sym
        assert matching[0]["status"] == "open"
        assert matching[0]["quantity"] == 100

        # 3. Check portfolio summary reflects open position
        res_sum = client.get("/api/portfolio/summary")
        assert res_sum.status_code == 200
        assert res_sum.json()["open_positions"] >= 1

        # 4. Close the open position at market price LKR 28.00
        res_close = client.post(f"/api/portfolio/positions/{pos_id}/close?exit_price=28.00")
        assert res_close.status_code == 200
        assert res_close.json()["status"] == "closed"
        expected_pnl = round((28.00 - 25.50) * 100, 2)
        assert res_close.json()["pnl"] == expected_pnl

        # Verify position is now in closed positions
        res_closed = client.get("/api/portfolio/positions?status=closed")
        assert res_closed.status_code == 200
        closed_matching = [p for p in res_closed.json() if p["id"] == pos_id]
        assert len(closed_matching) == 1
        assert closed_matching[0]["status"] == "closed"

    finally:
        # 5. Permanently remove the test position
        res_del = client.delete(f"/api/portfolio/positions/{pos_id}/permanent")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "deleted"

        # Verify it is completely removed from DB
        row = db_session.execute(
            text("SELECT id FROM app.portfolio_positions WHERE id = :id"),
            {"id": pos_id},
        ).fetchone()
        assert row is None


def test_portfolio_validation_errors(client):
    """Verify input validation errors for invalid trade parameters."""
    # Negative entry price
    res1 = client.post("/api/portfolio/positions", json={"symbol": "ABC.N0000", "entry_price": -5.0, "quantity": 100})
    assert res1.status_code == 400

    # Zero quantity
    res2 = client.post("/api/portfolio/positions", json={"symbol": "ABC.N0000", "entry_price": 50.0, "quantity": 0})
    assert res2.status_code == 400

    # Missing symbol
    res3 = client.post("/api/portfolio/positions", json={"symbol": "", "entry_price": 50.0, "quantity": 100})
    assert res3.status_code == 400


def test_watchlist_lifecycle(client, db_session):
    """Verify adding, listing, and permanently removing a watchlist item."""
    test_sym = "WATCHTEST.N0000"

    # 1. Add to watchlist
    res_add = client.post("/api/portfolio/watchlist", json={
        "symbol": test_sym,
        "reason": "Test breakout alert",
        "alert_price_above": 55.0,
        "alert_price_below": 45.0,
    })
    assert res_add.status_code == 200
    watch_id = res_add.json()["id"]

    try:
        # 2. Verify listing
        res_list = client.get("/api/portfolio/watchlist")
        assert res_list.status_code == 200
        items = res_list.json()
        matching = [w for w in items if w["id"] == watch_id]
        assert len(matching) == 1
        assert matching[0]["symbol"] == test_sym
        assert matching[0]["alert_price_above"] == 55.0

    finally:
        # 3. Remove from watchlist
        res_del = client.delete(f"/api/portfolio/watchlist/{watch_id}")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "removed"
