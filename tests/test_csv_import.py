import io
import datetime
import pytest
from starlette.testclient import TestClient
from sqlalchemy import text

from src.api.main import app
from src.db import SessionLocal

client = TestClient(app)


def test_csv_import_empty_file():
    """Verify that uploading an empty file returns HTTP 400."""
    response = client.post(
        "/api/data/import/csv",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_csv_import_invalid_columns():
    """Verify that CSV missing date/close columns returns HTTP 400."""
    invalid_csv = "colA,colB,colC\n1,2,3\n"
    response = client.post(
        "/api/data/import/csv",
        files={"file": ("test.csv", invalid_csv.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 400
    assert "date" in response.json()["detail"].lower()


def test_csv_import_5_years_historical_data():
    """Verify uploading 5 years of historical OHLCV data into core.fact_price_daily."""
    test_symbol = "TEST5Y.N0000"
    
    # Generate 5 years (approx 1,250 trading days) of mock OHLCV rows
    start_date = datetime.date(2021, 1, 1)
    end_date = datetime.date(2026, 1, 1)
    
    csv_rows = ["symbol,trading_date,open,high,low,close,volume,turnover,num_trades"]
    cur_date = start_date
    price = 100.0
    count = 0
    
    while cur_date <= end_date:
        # Skip weekends (Saturday=5, Sunday=6)
        if cur_date.weekday() < 5:
            open_p = round(price, 2)
            high_p = round(price + 2.0, 2)
            low_p = round(price - 1.5, 2)
            close_p = round(price + 0.5, 2)
            vol = 50000
            turnover = round(close_p * vol, 2)
            trades = 45
            csv_rows.append(f"{test_symbol},{cur_date},{open_p},{high_p},{low_p},{close_p},{vol},{turnover},{trades}")
            price = close_p
            count += 1
        cur_date += datetime.timedelta(days=1)
        
    csv_content = "\n".join(csv_rows)
    
    # Upload via the API endpoint
    response = client.post(
        "/api/data/import/csv",
        files={"file": ("test_5y_history.csv", csv_content.encode("utf-8"), "text/csv")},
        data={"recompute_features": "false"},  # Speed up unit test
    )
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["rows_imported"] == count
    assert test_symbol in data["unique_symbols"]
    assert data["date_range"]["min"] == "2021-01-01"
    
    # Verify records in the database
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT COUNT(*), MIN(p.trading_date), MAX(p.trading_date)
                FROM core.fact_price_daily p
                JOIN core.dim_security s ON s.security_id = p.security_id
                WHERE s.symbol = :sym
            """),
            {"sym": test_symbol},
        ).fetchone()
        
        assert row[0] == count
        assert str(row[1]) == "2021-01-01"
        assert str(row[2]) == "2026-01-01"
        
    finally:
        # Cleanup test data so database stays pristine
        db.execute(
            text("DELETE FROM core.fact_price_daily WHERE security_id IN (SELECT security_id FROM core.dim_security WHERE symbol = :sym)"),
            {"sym": test_symbol},
        )
        db.execute(
            text("DELETE FROM core.dim_security WHERE symbol = :sym"),
            {"sym": test_symbol},
        )
        db.commit()
        db.close()
