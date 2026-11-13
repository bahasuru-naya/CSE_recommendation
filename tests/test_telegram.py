import json
from datetime import date, datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest

from src.alerts.telegram import TelegramAlerter
from src.api.main import app
from src.db import get_db
from src.scheduler.jobs import PipelineScheduler


@patch("src.alerts.telegram.requests.post")
def test_send_message_returns_telegram_api_result(post):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"ok": True}
    post.return_value = response
    alerter = TelegramAlerter(bot_token="test-token", chat_id="123")

    assert alerter.send_message("hello") is True
    post.assert_called_once_with(
        "https://api.telegram.org/bottest-token/sendMessage",
        json={"chat_id": "123", "text": "hello"},
        timeout=10,
    )


@patch("src.alerts.telegram.requests.post")
def test_send_message_reports_telegram_api_error(post):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"ok": False, "description": "chat not found"}
    post.return_value = response
    alerter = TelegramAlerter(bot_token="test-token", chat_id="123")

    assert alerter.send_message("hello") is False


@patch("src.alerts.telegram.requests.post")
def test_send_message_reports_http_error(post):
    response = Mock()
    response.status_code = 400
    response.json.return_value = {"ok": False, "description": "chat not found"}
    post.return_value = response
    alerter = TelegramAlerter(bot_token="test-token", chat_id="123")

    assert alerter.send_message("hello") is False


@patch("src.alerts.telegram.requests.post")
def test_recommendation_escapes_html_and_sets_parse_mode(post):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"ok": True}
    post.return_value = response
    alerter = TelegramAlerter(bot_token="test-token", chat_id="123")

    assert alerter.send_recommendation({"symbol": "<ABC>", "signal": "BUY"}) is True

    payload = post.call_args.kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert "&lt;ABC&gt;" in payload["text"]


def test_test_alert_endpoint_sends_message(monkeypatch):
    sent = []

    class FakeAlerter:
        bot_token = "test-token"
        chat_id = "123"

        def __init__(self, **_kwargs):
            pass

        def send_message(self, message):
            sent.append(message)
            return True

    monkeypatch.setattr("src.api.routes.settings.TelegramAlerter", FakeAlerter)

    def fake_db():
        yield object()

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).post(
            "/api/settings/telegram/test",
            json={"bot_token": "test-token", "chat_id": "123"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    assert sent == ["CSE Recommendation: Telegram test alert sent successfully."]


def test_telegram_settings_update_keeps_token_hidden_and_saves_schedule():
    class FakeResult:
        def __init__(self, value):
            self.value = value

        def scalar(self):
            return self.value

    class FakeDB:
        value = {"bot_token": "saved-test-token", "chat_id": "123", "alert_time": "15:00"}

        def execute(self, query, params=None):
            if "SELECT value" in str(query):
                return FakeResult(self.value)
            self.value = json.loads(params["value"])
            return FakeResult(None)

        def commit(self):
            pass

    db = FakeDB()

    def fake_db():
        yield db

    app.dependency_overrides[get_db] = fake_db
    try:
        client = TestClient(app)
        updated = client.put(
            "/api/settings/telegram",
            json={"chat_id": "456", "alert_time": "16:30"},
        )
        current = client.get("/api/settings/telegram")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert updated.status_code == 200
    assert current.json() == {
        "bot_token_configured": True,
        "chat_id": "456",
        "alert_time": "16:30",
    }


@pytest.mark.asyncio
async def test_api_lifespan_starts_and_stops_scheduler(monkeypatch):
    from src.api import main as api_main

    calls = []

    class FakeScheduler:
        def start(self):
            calls.append("start")

        def stop(self):
            calls.append("stop")

    monkeypatch.setattr(api_main, "PipelineScheduler", FakeScheduler)

    async with api_main.lifespan(app):
        assert calls == ["start"]

    assert calls == ["start", "stop"]


def test_scheduler_registers_job_run_parent_rows(monkeypatch):
    registered = []

    class FakeSession:
        def execute(self, _query, params):
            registered.append(params["job_id"])

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("src.scheduler.jobs.SessionLocal", FakeSession)
    PipelineScheduler()._register_job_records()

    assert set(registered) == {"intraday_snapshot", "eod_fetch", "telegram_alerts"}


def test_scheduler_sends_again_when_daily_time_changes(monkeypatch):
    import src.scheduler.jobs as scheduler_jobs

    saved_settings = []
    schedule = {
        "bot_token": "saved-test-token",
        "chat_id": "123",
        "alert_time": "15:46",
        "last_sent_date": "2026-11-12",
        "last_sent_time": "15:00",
    }

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 12, 15, 47, tzinfo=tz)

    class FakeResult:
        def __init__(self, value):
            self.value = value

        def scalar(self):
            return self.value

    class FakeSession:
        def execute(self, query, params=None):
            sql = str(query)
            if "SELECT value" in sql:
                return FakeResult(schedule)
            if "SELECT EXISTS" in sql:
                return FakeResult(True)
            saved_settings.append(json.loads(params["value"]))
            return FakeResult(None)

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(scheduler_jobs, "datetime", FrozenDateTime)
    monkeypatch.setattr(scheduler_jobs, "SessionLocal", FakeSession)
    scheduler = PipelineScheduler()
    scheduler._last_telegram_alert_slot = (date(2026, 11, 12), "15:00")
    monkeypatch.setattr(scheduler, "job_telegram_alerts", lambda: {"sent": 3})

    scheduler._check_telegram_alert_schedule()

    assert saved_settings[0]["last_sent_time"] == "15:46"
