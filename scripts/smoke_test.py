"""CSE API Smoke Test

Hits all authentic Colombo Stock Exchange (CSE) API endpoints using HTTP POST
with form-url-encoded parameters, records status codes, timings, and
response shapes, then prints a summary table and saves full results
to ``smoke_test_results.json``.

Usage::

    python scripts/smoke_test.py
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import time
from typing import Any

import requests

# Ensure safe UTF-8 printing on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://www.cse.lk/api/"
TIMEOUT = 30  # seconds

# Complete catalogue of official CSE public endpoints (all POST)
ENDPOINTS: list[tuple[str, dict[str, Any] | None, str]] = [
    # Single company info & charts
    ("companyInfoSummery", {"symbol": "LOLC.N0000"}, "companyInfoSummery (LOLC.N0000)"),
    ("companyChartDataByStock", {"stockId": 378, "period": 1}, "companyChartDataByStock (stockId=378, period=1)"),
    ("companyChartDataByStock", {"stockId": 378, "period": 4}, "companyChartDataByStock (stockId=378, period=4)"),
    ("chartData", {"chartId": "1", "period": "1"}, "chartData (chartId=1, period=1)"),

    # Market-wide trade summaries & active boards
    ("tradeSummary", None, "tradeSummary (All Securities)"),
    ("todaySharePrice", None, "todaySharePrice"),
    ("topGainers", None, "topGainers"),
    ("topLooses", None, "topLooses"),
    ("mostActiveTrades", None, "mostActiveTrades"),
    ("detailedTrades", None, "detailedTrades"),

    # Indices and market summaries
    ("marketStatus", None, "marketStatus"),
    ("marketSummery", None, "marketSummery"),
    ("dailyMarketSummery", None, "dailyMarketSummery"),
    ("aspiData", None, "aspiData (ASPI Index)"),
    ("snpData", None, "snpData (S&P SL20 Index)"),
    ("allSectors", None, "allSectors"),

    # Announcements and corporate actions
    ("approvedAnnouncement", None, "approvedAnnouncement"),
    ("getFinancialAnnouncement", None, "getFinancialAnnouncement"),
    ("circularAnnouncement", None, "circularAnnouncement"),
    ("directiveAnnouncement", None, "directiveAnnouncement"),
    ("getNonComplianceAnnouncements", None, "getNonComplianceAnnouncements"),
    ("getNewListingsRelatedNoticesAnnouncements", None, "getNewListingsRelatedNoticesAnnouncements"),
    ("getBuyInBoardAnnouncements", None, "getBuyInBoardAnnouncements"),
]


def _first_keys(data: Any, n: int = 6) -> list[str]:
    """Extract first n keys from a dict or list-of-dicts response."""
    if isinstance(data, dict):
        return list(data.keys())[:n]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return list(data[0].keys())[:n]
    return []


def _probe(
    path: str,
    payload: dict[str, Any] | None,
    description: str,
    session: requests.Session,
) -> dict[str, Any]:
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    result: dict[str, Any] = {
        "description": description,
        "method": "POST",
        "url": url,
        "payload": payload,
        "status": None,
        "response_bytes": 0,
        "response_time_ms": 0,
        "first_keys": [],
        "error": None,
        "ok": False,
    }

    start = time.perf_counter()
    try:
        resp = session.post(url, data=payload or {}, timeout=TIMEOUT)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        result["status"] = resp.status_code
        result["response_bytes"] = len(resp.content)
        result["response_time_ms"] = elapsed_ms

        if resp.status_code == 200:
            result["ok"] = True
            try:
                parsed = resp.json()
                result["first_keys"] = _first_keys(parsed)
            except ValueError:
                result["first_keys"] = ["<non-json>"]
        else:
            result["error"] = resp.text[:200]

    except requests.RequestException as exc:
        result["error"] = str(exc)

    return result


def run_smoke_test() -> list[dict[str, Any]]:
    print("\n[+] CSE API Smoke Test (POST Form-Url-Encoded)\n")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Referer": "https://www.cse.lk/",
    })

    results = []
    for path, payload, desc in ENDPOINTS:
        res = _probe(path, payload, desc, session)
        results.append(res)
        mark = "[PASS]" if res["ok"] else "[FAIL]"
        status_str = f"HTTP {res['status']}" if res["status"] else "CONN_ERR"
        print(f"  {mark:<6} {desc:<45} {status_str:<10} {res['response_time_ms']:>6.0f}ms {res['response_bytes']:>8} B")

    passed = sum(1 for r in results if r["ok"])
    total = len(results)

    print("\n" + "=" * 95)
    print(f"  SMOKE TEST SUMMARY: {passed}/{total} passed, {total - passed} failed")
    print("=" * 95)
    print(f"  {'Status':<8} {'Endpoint':<45} {'HTTP':<8} {'Time(ms)':<10} {'Size':<10} {'Keys'}")
    print("-" * 95)
    for r in results:
        status_str = str(r["status"] or "ERR")
        keys_str = ", ".join(r["first_keys"]) if r["first_keys"] else (r["error"] or "")[:35]
        mark = "[PASS]" if r["ok"] else "[FAIL]"
        print(f"  {mark:<8} {r['description']:<43} {status_str:<8} {r['response_time_ms']:>6.0f}ms {r['response_bytes']:>8} B  {keys_str}")
    print("=" * 95)

    out_file = Path(__file__).resolve().parent.parent / "smoke_test_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved full results to: {out_file}\n")

    return results


if __name__ == "__main__":
    run_smoke_test()
