"""Endpoint registry for the CSE unofficial API.

Every endpoint the pipeline consumes is declared here with its URL path,
expected parameters, response shape, and a mapping from the API's field
names to our internal (staging-table) column names.

When the API changes, update *this* file only — the rest of the pipeline
adapts automatically.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ENDPOINT_REGISTRY: dict[str, dict] = {
    # ── Market-wide trade summary ─────────────────────────────────────────
    "trade_summary": {
        "path": "tradeSummary",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "stock_id",
            "symbol": "symbol",
            "name": "name",
            "lastTradedPrice": "last_traded_price",
            "priceChange": "change",
            "percentageChange": "change_percentage",
            "volume": "volume",
            "turnover": "turnover",
            "high": "high",
            "low": "low",
            "openPrice": "open_price",
            "previousClose": "previous_close",
            "noOfTrades": "num_trades",
            "marketCap": "market_cap",
            "sharesInIssue": "shares_in_issue",
            "fiftyTwoWeekHigh": "week_52_high",
            "fiftyTwoWeekLow": "week_52_low",
            "buyQuantity": "buy_quantity",
            "sellQuantity": "sell_quantity",
            "status": "trade_status",
        },
    },
    # ── Company info ──────────────────────────────────────────────────────
    "company_info": {
        "path": "companyInfoSummery",
        "method": "POST",
        "params_template": {"symbol": "{symbol}"},
        "response_type": "object",
        "field_mappings": {
            "symbol": "symbol",
            "companyName": "company_name",
            "industry": "industry",
            "sector": "sector",
            "marketCap": "market_cap",
            "price": "price",
            "change": "change",
            "changePercentage": "change_percentage",
            "volume": "volume",
            "turnover": "turnover",
            "high": "high",
            "low": "low",
            "openPrice": "open_price",
            "previousClose": "previous_close",
            "noOfTrades": "num_trades",
            "beta": "beta",
            "eps": "eps",
            "per": "pe_ratio",
            "pbv": "pb_ratio",
            "dividendYield": "dividend_yield",
            "sharesInIssue": "shares_in_issue",
            "fiftyTwoWeekHigh": "week_52_high",
            "fiftyTwoWeekLow": "week_52_low",
            "status": "trade_status",
            "boardType": "board_type",
            "lastTradedDate": "last_traded_date",
        },
    },
    # ── Chart data (index-level) ──────────────────────────────────────────
    "chart_data": {
        "path": "chartData",
        "method": "POST",
        "params_template": {"symbol": "{symbol}", "chartId": "CHART_BY_CLOSE", "period": "{period}"},
        "response_type": "list",
        "field_mappings": {
            "date": "trading_date",
            "open": "open_price",
            "high": "high",
            "low": "low",
            "close": "close_price",
            "volume": "volume",
            "turnover": "turnover",
        },
    },
    # ── Company-level chart data ──────────────────────────────────────────
    "company_chart_data": {
        "path": "companyChartDataByStock",
        "method": "POST",
        "params_template": {"stockId": "{stock_id}", "period": "{period}"},
        "response_type": "list",
        "field_mappings": {
            "date": "trading_date",
            "open": "open_price",
            "high": "high",
            "low": "low",
            "close": "close_price",
            "volume": "volume",
            "turnover": "turnover",
        },
    },
    # ── Today's share prices ──────────────────────────────────────────────
    "today_share_price": {
        "path": "todaySharePrice",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "stock_id",
            "symbol": "symbol",
            "name": "name",
            "lastTradedPrice": "last_traded_price",
            "priceChange": "change",
            "percentageChange": "change_percentage",
            "volume": "volume",
            "turnover": "turnover",
            "high": "high",
            "low": "low",
            "openPrice": "open_price",
            "previousClose": "previous_close",
            "noOfTrades": "num_trades",
        },
    },
    # ── Top gainers ───────────────────────────────────────────────────────
    "top_gainers": {
        "path": "topGainers",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "stock_id",
            "symbol": "symbol",
            "name": "name",
            "lastTradedPrice": "last_traded_price",
            "priceChange": "change",
            "percentageChange": "change_percentage",
            "volume": "volume",
            "turnover": "turnover",
        },
    },
    # ── Top losers ────────────────────────────────────────────────────────
    "top_losers": {
        "path": "topLosers",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "stock_id",
            "symbol": "symbol",
            "name": "name",
            "lastTradedPrice": "last_traded_price",
            "priceChange": "change",
            "percentageChange": "change_percentage",
            "volume": "volume",
            "turnover": "turnover",
        },
    },
    # ── Most active by trades ─────────────────────────────────────────────
    "most_active_trades": {
        "path": "mostActiveTrades",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "stock_id",
            "symbol": "symbol",
            "name": "name",
            "lastTradedPrice": "last_traded_price",
            "priceChange": "change",
            "percentageChange": "change_percentage",
            "volume": "volume",
            "turnover": "turnover",
            "noOfTrades": "num_trades",
        },
    },
    # ── Market status (open / closed) ─────────────────────────────────────
    "market_status": {
        "path": "marketStatus",
        "method": "POST",
        "params": {},
        "response_type": "object",
        "field_mappings": {
            "status": "market_status",
            "dateTime": "status_datetime",
            "message": "status_message",
        },
    },
    # ── Market summary ────────────────────────────────────────────────────
    "market_summary": {
        "path": "marketSummery",
        "method": "POST",
        "params": {},
        "response_type": "object",
        "field_mappings": {
            "aspiIndex": "aspi_index",
            "aspiChange": "aspi_change",
            "aspiPercentageChange": "aspi_change_pct",
            "snpIndex": "snp_index",
            "snpChange": "snp_change",
            "snpPercentageChange": "snp_change_pct",
            "totalTurnover": "total_turnover",
            "totalVolume": "total_volume",
            "totalTrades": "total_trades",
            "marketCap": "total_market_cap",
            "marketStatus": "market_status",
            "dateTime": "summary_datetime",
        },
    },
    # ── Daily market summary (historical) ─────────────────────────────────
    "daily_market_summary": {
        "path": "dailyMarketSummery",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "date": "trading_date",
            "aspiIndex": "aspi_index",
            "aspiChange": "aspi_change",
            "aspiPercentageChange": "aspi_change_pct",
            "snpIndex": "snp_index",
            "snpChange": "snp_change",
            "snpPercentageChange": "snp_change_pct",
            "totalTurnover": "total_turnover",
            "totalVolume": "total_volume",
            "totalTrades": "total_trades",
        },
    },
    # ── ASPI chart data ───────────────────────────────────────────────────
    "aspi_data": {
        "path": "aspiData",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "date": "trading_date",
            "value": "aspi_value",
            "change": "aspi_change",
            "percentageChange": "aspi_change_pct",
            "volume": "volume",
            "turnover": "turnover",
        },
    },
    # ── S&P SL20 chart data ───────────────────────────────────────────────
    "snp_data": {
        "path": "snpData",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "date": "trading_date",
            "value": "snp_value",
            "change": "snp_change",
            "percentageChange": "snp_change_pct",
            "volume": "volume",
            "turnover": "turnover",
        },
    },
    # ── All sectors ───────────────────────────────────────────────────────
    "all_sectors": {
        "path": "allSectors",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "sectorName": "sector_name",
            "sectorIndex": "sector_index",
            "sectorChange": "sector_change",
            "sectorPercentageChange": "sector_change_pct",
            "turnover": "turnover",
            "volume": "volume",
            "noOfTrades": "num_trades",
            "marketCap": "market_cap",
        },
    },
    # ── Detailed trades ───────────────────────────────────────────────────
    "detailed_trades": {
        "path": "detailedTrades",
        "method": "POST",
        "params_template": {"symbol": "{symbol}"},
        "response_type": "list",
        "field_mappings": {
            "tradeId": "trade_id",
            "symbol": "symbol",
            "price": "price",
            "quantity": "quantity",
            "time": "trade_time",
            "buyBrokerId": "buy_broker_id",
            "sellBrokerId": "sell_broker_id",
        },
    },
    # ── Announcements ─────────────────────────────────────────────────────
    "approved_announcements": {
        "path": "approvedAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "company": "company",
            "symbol": "symbol",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
        },
    },
    "financial_announcements": {
        "path": "financialAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "company": "company",
            "symbol": "symbol",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
            "period": "reporting_period",
            "year": "reporting_year",
        },
    },
    "circular_announcements": {
        "path": "circularAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
        },
    },
    "directive_announcements": {
        "path": "directiveAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
        },
    },
    "covid_announcements": {
        "path": "covidAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "company": "company",
            "symbol": "symbol",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
        },
    },
    "non_compliance_announcements": {
        "path": "nonComplianceAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "company": "company",
            "symbol": "symbol",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
            "reason": "non_compliance_reason",
        },
    },
    "new_listings_announcements": {
        "path": "newListingsAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "company": "company",
            "symbol": "symbol",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
            "listingDate": "listing_date",
            "boardType": "board_type",
        },
    },
    "buy_in_board_announcements": {
        "path": "buyInBoardAnnouncements",
        "method": "POST",
        "params": {},
        "response_type": "list",
        "field_mappings": {
            "id": "announcement_id",
            "title": "title",
            "company": "company",
            "symbol": "symbol",
            "date": "announcement_date",
            "description": "description",
            "url": "url",
            "type": "announcement_type",
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_endpoint(name: str) -> dict:
    """Return the endpoint config for *name*, raising ``KeyError`` if unknown."""
    if name not in ENDPOINT_REGISTRY:
        raise KeyError(f"Unknown endpoint: {name!r}. Known: {sorted(ENDPOINT_REGISTRY)}")
    return ENDPOINT_REGISTRY[name]


def resolve_params(name: str, **kwargs: str) -> dict[str, str]:
    """Build the final POST data dict for an endpoint.

    Template placeholders like ``{symbol}`` in ``params_template`` are
    filled from *kwargs*.  If the endpoint has a static ``params`` dict
    that is returned directly.
    """
    ep = get_endpoint(name)
    if "params_template" in ep:
        template = ep["params_template"]
        resolved: dict[str, str] = {}
        for key, val in template.items():
            if val.startswith("{") and val.endswith("}"):
                placeholder = val[1:-1]
                if placeholder not in kwargs:
                    raise ValueError(
                        f"Missing required param {placeholder!r} for endpoint {name!r}"
                    )
                resolved[key] = kwargs[placeholder]
            else:
                resolved[key] = val
        return resolved
    return dict(ep.get("params", {}))


def get_field_mappings(name: str) -> dict[str, str]:
    """Return ``{api_field: staging_column}`` mappings for an endpoint."""
    return dict(get_endpoint(name).get("field_mappings", {}))


def list_endpoints() -> list[str]:
    """Return sorted list of all registered endpoint names."""
    return sorted(ENDPOINT_REGISTRY.keys())
