"""Generic and robust parser for transforming raw CSE API payloads into staging-layer rows."""

from __future__ import annotations

from datetime import date, datetime, timezone
import logging
from typing import Any

from src.ingestion.endpoints import ENDPOINT_REGISTRY
from src.utils.time_utils import trading_date

logger = logging.getLogger(__name__)


def safe_float(val: Any) -> float | None:
    """Convert value safely to float or None."""
    if val is None or val == "" or val == "-":
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val: Any) -> int | None:
    """Convert value safely to int or None."""
    if val is None or val == "" or val == "-":
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return int(float(val))
    except (ValueError, TypeError):
        return None


def parse_trade_summary_item(item: dict[str, Any], default_trading_date: date | None = None) -> dict[str, Any]:
    """Parse one item from CSE tradeSummary endpoint into staging.trade_summary row."""
    mapping = ENDPOINT_REGISTRY.get("trade_summary", {}).get("field_mappings", {})
    t_date = default_trading_date or trading_date()

    return {
        "symbol": str(item.get("symbol") or item.get("securityCode") or "").strip().upper(),
        "name": item.get("name") or item.get("companyName"),
        "last_traded_price": safe_float(item.get("lastTradedPrice") or item.get("price")),
        "change": safe_float(item.get("priceChange") or item.get("change")),
        "change_percentage": safe_float(item.get("percentageChange") or item.get("changePercentage")),
        "volume": safe_int(item.get("volume") or item.get("shareVolume")),
        "turnover": safe_float(item.get("turnover")),
        "high": safe_float(item.get("high") or item.get("highPrice")),
        "low": safe_float(item.get("low") or item.get("lowPrice")),
        "open_price": safe_float(item.get("openPrice") or item.get("open")),
        "previous_close": safe_float(item.get("previousClose") or item.get("closingPrice")),
        "num_trades": safe_int(item.get("noOfTrades") or item.get("trades")),
        "market_cap": safe_float(item.get("marketCap")),
        "trading_date": t_date,
    }


def parse_company_info(symbol: str, raw_data: dict[str, Any]) -> dict[str, Any]:
    """Parse response from companyInfoSummery into staging.company_info row."""
    sym_info = raw_data.get("reqSymbolInfo") or raw_data.get("symbolInfo") or raw_data
    beta_info = raw_data.get("reqSymbolBetaInfo") or raw_data.get("betaInfo") or {}

    return {
        "symbol": symbol.strip().upper(),
        "name": sym_info.get("name") or sym_info.get("companyName"),
        "isin": sym_info.get("isin"),
        "sector": sym_info.get("sector") or sym_info.get("sectorName"),
        "industry": sym_info.get("industry"),
        "market_cap": safe_float(sym_info.get("marketCap")),
        "last_traded_price": safe_float(sym_info.get("lastTradedPrice")),
        "change": safe_float(sym_info.get("change")),
        "change_percentage": safe_float(sym_info.get("changePercentage")),
        "beta_spsl": safe_float(beta_info.get("betaValueSPSL") or beta_info.get("betaSPSL")),
        "beta_aspi": safe_float(beta_info.get("betaValueASPI") or beta_info.get("betaASPI")),
        "shares_outstanding": safe_int(sym_info.get("sharesOutstanding") or sym_info.get("sharesInIssue")),
        "listed_date": None,
        "raw_data": raw_data,
    }


def parse_chart_data(symbol: str, stock_id: int | None, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse chartData / companyChartDataByStock list of points into staging.chart_data rows."""
    rows = []
    for pt in records:
        # Date can be string or timestamp integer
        d_val = pt.get("date") or pt.get("tradingDate") or pt.get("t")
        parsed_date = None
        if isinstance(d_val, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y%m%d"):
                try:
                    parsed_date = datetime.strptime(d_val[:10], fmt).date()
                    break
                except ValueError:
                    continue
        elif isinstance(d_val, (int, float)):
            # Epoch milliseconds or seconds
            if d_val > 10_000_000_000:
                parsed_date = datetime.fromtimestamp(d_val / 1000.0, tz=timezone.utc).date()
            else:
                parsed_date = datetime.fromtimestamp(d_val, tz=timezone.utc).date()

        if not parsed_date:
            continue

        close_price = safe_float(pt.get("close") or pt.get("price") or pt.get("p") or pt.get("c") or pt.get("lastTradedPrice"))
        open_price = safe_float(pt.get("open") or pt.get("o")) or close_price
        high = safe_float(pt.get("high") or pt.get("h")) or close_price
        low = safe_float(pt.get("low") or pt.get("l")) or close_price
        volume = safe_int(pt.get("volume") or pt.get("v") or pt.get("q")) or 0
        turnover = safe_float(pt.get("turnover")) or (close_price * volume if close_price else 0.0)

        rows.append({
            "symbol": symbol.strip().upper(),
            "stock_id": stock_id,
            "trading_date": parsed_date,
            "open_price": open_price,
            "high": high,
            "low": low,
            "close_price": close_price,
            "volume": volume,
            "turnover": turnover,
            "num_trades": safe_int(pt.get("trades") or pt.get("numTrades")),
        })
    return rows


def parse_market_summary(
    trading_date: date,
    aspi_data: dict[str, Any] | None = None,
    snp_data: dict[str, Any] | None = None,
    summary_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse ASPI, S&P SL20, and overall market summary."""
    aspi_val = safe_float(aspi_data.get("indexValue") or aspi_data.get("value")) if aspi_data else None
    aspi_chg = safe_float(aspi_data.get("change")) if aspi_data else None
    aspi_pct = safe_float(aspi_data.get("percentage") or aspi_data.get("changePercentage")) if aspi_data else None

    snp_val = safe_float(snp_data.get("indexValue") or snp_data.get("value")) if snp_data else None
    snp_chg = safe_float(snp_data.get("change")) if snp_data else None
    snp_pct = safe_float(snp_data.get("percentage") or snp_data.get("changePercentage")) if snp_data else None

    summ = summary_data or {}
    return {
        "trading_date": trading_date,
        "aspi_value": aspi_val,
        "aspi_change": aspi_chg,
        "aspi_change_pct": aspi_pct,
        "snp_value": snp_val,
        "snp_change": snp_chg,
        "snp_change_pct": snp_pct,
        "total_turnover": safe_float(summ.get("turnover") or summ.get("totalTurnover")),
        "total_volume": safe_int(summ.get("volume") or summ.get("totalVolume")),
        "total_trades": safe_int(summ.get("trades") or summ.get("totalTrades")),
        "market_cap": safe_float(summ.get("marketCap") or summ.get("totalMarketCap")),
    }
