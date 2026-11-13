import threading
import time

from src.ingestion.connectors.chart_data import ChartDataConnector
from src.ingestion.client import CSEApiClient


class SessionStub:
    def execute(self, *_args, **_kwargs):
        return None

    def commit(self):
        pass


def test_sync_symbols_reports_per_symbol_progress_and_failures(monkeypatch):
    connector = ChartDataConnector(SessionStub(), client=object())

    def fetch(symbol, stock_id, _period, _client):
        return {
            "endpoint": "chartData",
            "params": {"symbol": symbol},
            "records": [{"symbol": symbol}],
            "status_code": 200,
            "elapsed_ms": 1,
            "error": None,
        }

    monkeypatch.setattr(connector, "_fetch_symbol_chart", fetch)
    monkeypatch.setattr(
        connector,
        "_stage_fetched_chart",
        lambda symbol, _stock_id, _result: 5 if symbol == "AAA" else 0,
    )
    progress = []

    result = connector.sync_symbols(
        [("AAA", 1), ("BBB", 2)],
        progress_callback=lambda *values: progress.append(values),
    )

    assert result["symbols_processed"] == 2
    assert result["symbols_succeeded"] == 1
    assert result["total_points"] == 5
    assert result["successful_symbols"] == ["AAA"]
    assert result["failed_symbols"] == [{"symbol": "BBB", "error": "No chart rows were staged"}]
    assert [(event[0], event[1], event[3]) for event in progress] == [
        (1, 2, 5),
        (2, 2, 0),
    ]


def test_sync_symbols_fetches_with_bounded_concurrency(monkeypatch):
    client = CSEApiClient()
    connector = ChartDataConnector(SessionStub(), client=client)
    lock = threading.Lock()
    active_requests = 0
    max_active_requests = 0

    def fake_post(_client, _endpoint, data=None):
        nonlocal active_requests, max_active_requests
        with lock:
            active_requests += 1
            max_active_requests = max(max_active_requests, active_requests)
        time.sleep(0.03)
        with lock:
            active_requests -= 1
        return {
            "status": 200,
            "data": [{"symbol": data["symbol"]}],
            "elapsed_ms": 1,
        }

    monkeypatch.setattr(CSEApiClient, "post", fake_post)
    monkeypatch.setattr(connector, "_stage_fetched_chart", lambda *_args: 1)

    try:
        result = connector.sync_symbols([(f"SYM{idx}", idx) for idx in range(8)])
    finally:
        client.close()

    assert result["symbols_succeeded"] == 8
    assert max_active_requests > 1
    assert max_active_requests <= 4
