# CSE Stock Recommendation System

An end-to-end data pipeline and ML-powered stock recommendation engine for the **Colombo Stock Exchange (CSE)**. The system ingests live market data, engineers 25+ trading features, scores stocks with LightGBM + SHAP, and delivers transparent, explainable recommendations via a React dashboard and REST API.

> **Free & local** — runs entirely on your own PC. No paid APIs, no cloud services. PostgreSQL 16 + TimescaleDB medallion data lake, Python 3.12, React 18.

---



### Database Schemas (Medallion Lake)

| Schema | Purpose |
|---|---|
| `raw` | Raw API payloads (JSONB), ingestion run log |
| `staging` | Type-cast, deduplicated per-dataset tables |
| `core` | Canonical OHLCV facts, company dim, calendar dim (hypertables) |
| `features` | Versioned feature sets (25+ signals, security × date) |
| `ml` | Model registry, training runs, predictions, backtests, drift metrics |
| `app` | Recommendation snapshots, portfolio positions, watchlist, job audit log |

---

## Current State (November 2026)

| Metric | Value |
|---|---|
| Securities tracked | ~291 (all CSE listed stocks) |
| Securities with logos | 49+ (synced from CSE CDN) |
| Price records | 1,316+ daily OHLCV rows |
| Engineered features | 25 per security × date |
| Model versions | 2 (LightGBM binary classifier) |
| Active recommendations | 25 per daily run |
| Recommendation format | Structured SHAP explainability payload |

---

## Prerequisites

| Dependency | Version | Notes |
|---|---|---|
| Python | ≥ 3.12 | `type` statement, f-string improvements |
| PostgreSQL | 16 | TimescaleDB-compatible |
| TimescaleDB | Community (free) | Native install or Docker |
| Node.js | ≥ 18 | For the React dashboard |
| Docker Compose | v2 | Optional — for the DB container only |

---

## Quick Start

### 1 — Database

```bash
# Option A: Docker (easiest)
docker compose up -d           # starts timescale/timescaledb container

# Option B: Native
# Install PostgreSQL 16 + TimescaleDB extension, then:
# createdb cse_lake
```

### 2 — Python backend

```bash
cd d:\Myfiles\Bahasuru\BOC\Projects\CSE_recommndation

# Create virtualenv and install
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env → set DB_URL, TELEGRAM_BOT_TOKEN (optional)

# Bootstrap database schemas + run Alembic migrations
python -m scripts.setup_db
alembic upgrade head

# Optional: sync company logos from CSE CDN → DB
python -m scripts.sync_company_logos
```

### 3 — Run the pipeline

```bash
# Backfill historical prices (period 1-5 selects CSE chart period)
python -m src.main backfill --period 4

# Run daily pipeline (ingest → features → score → recommendations)
python -m src.main daily

# Retrain the LightGBM model
python -m src.main retrain

# Reconcile portfolio positions (mark executed, update prices)
python -m src.main reconcile

# Start the FastAPI server
python -m src.main serve
# → http://127.0.0.1:8000

uvicorn src.api.main:app --reload --port 8000
```

### 4 — React dashboard

```bash
cd dashboard
npm install
npm run dev      # development → http://localhost:5173
npm run build    # production build → dashboard/dist/
```

---

## Project Structure

```
CSE_recommndation/
├── .env.example                    # Environment variable template
├── .env                            # Local config (gitignored)
├── docker-compose.yml              # TimescaleDB container
├── pyproject.toml                  # Project metadata & dependencies
├── README.md                       # ← you are here
│
├── alembic/                        # Database migrations
│   └── versions/
│       ├── 001_create_raw_layer.py
│       ├── 002_create_staging_layer.py
│       ├── 003_create_core_layer.py    # dim_security (logo_url), hypertables
│       ├── 004_create_features_layer.py
│       ├── 005_create_ml_layer.py
│       └── 006_create_app_layer.py     # recommendations (logo_url, reasons JSONB)
│
├── scripts/
│   ├── setup_db.py                 # One-time DB bootstrap
│   ├── smoke_test.py               # CSE API endpoint health check
│   ├── add_logo_column.py          # Adds logo_url columns (migration helper)
│   ├── sync_company_logos.py       # Bulk-syncs logos from CSE CDN → DB
│   └── sync_heavyweights.py        # Syncs top-15 stocks logos
│
├── src/
│   ├── config.py                   # Pydantic Settings (reads .env)
│   ├── db.py                       # SQLAlchemy engine + session
│   ├── main.py                     # CLI entry point (backfill/daily/retrain/serve)
│   │
│   ├── ingestors/                  # CSE API clients (POST form-encoded)
│   │   ├── prices.py               # OHLCV price ingestion
│   │   ├── company_info.py         # Company details + logo path
│   │   └── market.py               # Market summary, indices
│   │
│   ├── core/
│   │   ├── calendar.py             # dim_calendar population (Asia/Colombo)
│   │   └── securities.py           # dim_security upserts
│   │
│   ├── features/
│   │   └── engineer.py             # 25+ technical indicators (RSI, MACD, ATR, …)
│   │
│   ├── ml/
│   │   ├── lgbm_model.py           # LightGBM train/predict + SHAP values
│   │   └── trainer.py              # Training pipeline with walk-forward CV
│   │
│   ├── engine/
│   │   ├── decision.py             # Signal generation + structured SHAP reasons
│   │   └── recommendations.py      # Save/load recommendations (logo_url, reasons)
│   │
│   └── api/
│       ├── main.py                 # FastAPI app + CORS
│       └── routes/
│           ├── recommendations.py  # GET /api/recommendations/ (logo_url, reasons)
│           ├── portfolio.py        # Positions, watchlist (logo_url)
│           └── data.py             # Securities, pipeline trigger
│
└── dashboard/                      # React 18 + Vite frontend
    └── src/
        ├── App.jsx
        ├── api/client.js           # TanStack Query hooks
        └── components/
            ├── CompanyLogo.jsx     # Logo img with gradient-avatar fallback
            ├── ExplainabilityModal.jsx  # SHAP waterfall + risk/reward modal
            ├── RecommendationCard.jsx   # Card with logo + Explain button
            ├── PortfolioTable.jsx  # Positions table with logos
            ├── PriceChart.jsx      # Recharts OHLCV chart
            ├── DataStatus.jsx      # Pipeline status panel
            ├── Layout.jsx
            └── Sidebar.jsx
```

---

## Key Features

### Transparent Explainability

Every recommendation includes a **structured SHAP reasons payload**:

```json
{
  "summary": "ABAN.N0000 scores above the alpha hurdle in a BULLISH market regime...",
  "factors": [
    { "feature": "rsi_14", "display_name": "RSI (14-day)", "value": 38.2,
      "impact": 0.047, "direction": "bullish", "description": "Oversold territory..." }
  ],
  "regime":    { "regime": "BULLISH", "aspi": 12850, "sma_200": 11200 },
  "liquidity": { "pass": true, "avg_turnover_lkr": 4200000, "threshold": 500000 },
  "risk_reward": { "entry": 42.5, "stop": 40.1, "target": 48.0, "rr_ratio": 2.3 },
  "model_details": { "model_version": "v2", "confidence": 0.74, "hurdle_rate": 0.0268 }
}
```

Click **Explain** on any recommendation card to open a full modal showing:
- Executive summary in plain English
- SHAP feature attribution waterfall (bullish vs bearish contributors)
- Risk/reward grid (entry, stop-loss, target, R:R ratio)
- Market regime context (ASPI vs 200-day SMA)
- Liquidity guardrail status
- Audit disclaimer (all orders placed manually through broker)

### Company Logos

Logos are fetched from the CSE CDN: `https://cdn.cse.lk/cmt/upload_logo/{path}`

The `CompanyLogo` component displays the actual logo with a graceful fallback to a colour-coded gradient avatar (derived from the ticker symbol) when no logo URL is available.

### Medallion Data Lake

Six-schema PostgreSQL layout with TimescaleDB hypertables for OHLCV facts. All writes are idempotent upserts. Timestamps are stored in UTC; a Colombo trading date column is added for local-calendar alignment. Point-in-time safety is enforced — forward-looking returns only appear in model targets, never in features.

---

## CLI Reference

```bash
python -m src.main backfill --period <1-5>   # Historical price backfill
python -m src.main daily                     # Full daily pipeline run
python -m src.main retrain                   # Retrain LightGBM model
python -m src.main reconcile                 # Reconcile portfolio positions
python -m src.main serve                     # Start FastAPI server (port 8000)
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/recommendations/latest` | GET | Latest scored recommendations (with logo_url, reasons) |
| `/api/recommendations/{id}` | GET | Single recommendation detail |
| `/api/recommendations/{id}/execute` | POST | Mark as executed |
| `/api/portfolio/positions` | GET | Open positions (with logo_url) |
| `/api/portfolio/watchlist` | GET | Watchlist (with logo_url) |
| `/api/data/securities` | GET | All tracked securities (with logo_url) |
| `/api/data/pipeline/run` | POST | Trigger pipeline run (`?target=daily`) |
| `/api/data/pipeline/status` | GET | Pipeline run status |

---

## Development

### Code Style

```bash
ruff check src/ scripts/           # Lint
ruff check --fix src/ scripts/     # Auto-fix
mypy src/                          # Type checking
```

### Database Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1               # Roll back one step
```

### Logo Sync

```bash
# Sync logos for all securities (fetches from CSE API → stores CDN URL in DB)
python -m scripts.sync_company_logos

# Sync major heavyweights only
python -m scripts.sync_heavyweights
```

---

## Key Design Decisions

1. **TimescaleDB** — Hypertables give automatic time-partitioning and fast range queries for OHLCV facts.
2. **Six-schema medallion layout** (`raw → staging → core → features → ml → app`) — isolates concerns, makes reprocessing safe, and enforces point-in-time integrity.
3. **CSE API uses POST with `application/x-www-form-urlencoded`** — not GET. All ingestors follow this pattern.
4. **LightGBM + SHAP** — Fast gradient-boosted tree model with TreeExplainer for per-prediction feature attribution.
5. **Human-in-the-loop** — The system generates trade parameters (entry, stop-loss, target, quantity) but all orders are placed manually by the user through their broker. The dashboard displays this disclaimer prominently.
6. **Pydantic v2** — Config and data validation throughout.
7. **Idempotent upserts** — All ingestion and feature writes use `INSERT ... ON CONFLICT DO UPDATE`, safe to re-run.
8. **Free, local, zero-cost** — No paid APIs, no cloud dependencies. Runs on a developer workstation.
