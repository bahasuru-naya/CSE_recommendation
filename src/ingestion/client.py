"""Resilient HTTP client for the CSE (Colombo Stock Exchange) unofficial API."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import get_settings

logger = logging.getLogger(__name__)


class CSEApiClient:
    """Resilient HTTP client for CSE API with retry logic.

    The CSE unofficial API uses POST for all endpoints and expects
    ``application/x-www-form-urlencoded`` content-type.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 30):
        settings = get_settings()
        self.base_url = (base_url or settings.cse_api_base_url).rstrip("/") + "/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Referer": "https://www.cse.lk/",
                "Origin": "https://www.cse.lk",
            }
        )

    # ── Core request ──────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """POST to a CSE API endpoint with automatic retry.

        Parameters
        ----------
        endpoint:
            Relative path appended to ``base_url`` (e.g. ``"tradeSummary"``).
        data:
            Form data to send in the POST body.

        Returns
        -------
        dict
            ``{"status": <http_status>, "data": <parsed_json>, "elapsed_ms": <int>}``
        """
        url = f"{self.base_url}{endpoint}"
        logger.debug("POST %s  data=%s", url, data)

        start = time.perf_counter()
        try:
            resp = self.session.post(url, data=data or {}, timeout=self.timeout)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
        except requests.RequestException:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.error("Request failed for %s after %d ms", endpoint, elapsed_ms)
            raise

        logger.debug(
            "Response %s  status=%d  size=%d  elapsed=%dms",
            endpoint,
            resp.status_code,
            len(resp.content),
            elapsed_ms,
        )

        # Attempt JSON parse; fall back to raw text wrapped in a dict
        try:
            body = resp.json()
        except ValueError:
            body = {"_raw_text": resp.text}

        return {
            "status": resp.status_code,
            "data": body,
            "elapsed_ms": elapsed_ms,
        }

    # ── Convenience methods ───────────────────────────────────────────────

    def fetch(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Shortcut that returns just the parsed data payload.

        Raises
        ------
        RuntimeError
            When the HTTP status is not 200.
        """
        result = self.post(endpoint, data)
        if result["status"] != 200:
            raise RuntimeError(
                f"CSE API returned status {result['status']} for {endpoint}"
            )
        return result["data"]

    def health_check(self) -> dict[str, Any]:
        """Quick check if the CSE API is reachable.

        Returns
        -------
        dict
            ``{"reachable": bool, "status": int | None, "elapsed_ms": int, "error": str | None}``
        """
        try:
            result = self.post("marketSummery")
            return {
                "reachable": result["status"] == 200,
                "status": result["status"],
                "elapsed_ms": result["elapsed_ms"],
                "error": None,
            }
        except Exception as exc:
            return {
                "reachable": False,
                "status": None,
                "elapsed_ms": 0,
                "error": str(exc),
            }

    def close(self) -> None:
        """Close the underlying requests session."""
        self.session.close()

    def __enter__(self) -> CSEApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
