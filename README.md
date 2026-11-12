# LankaAlpha AI — Colombo Stock Exchange Quantitative Intelligence

An end-to-end quantitative trading, lakehouse data pipeline, and machine learning recommendation engine engineered specifically for the **Colombo Stock Exchange (CSE)**. 

The platform ingests live and historical market data, engineers 25+ technical and fundamental alpha factors, trains leak-free gradient-boosted models (LightGBM + TreeSHAP), and delivers transparent, risk-managed stock signals through an interactive React dashboard and high-performance FastAPI service.

> **Free, Local & Self-Hosted** — Operates entirely on your own machine. Zero paid API keys, zero cloud vendor lock-in. Powered by PostgreSQL 16 + TimescaleDB (Medallion Lakehouse), Python 3.12, and React 18 + Tailwind CSS.

---

## Architecture Overview

```
                      COLOMBO STOCK EXCHANGE (CSE)
                                   │
              POST Form-Encoded API & Historical CSV Archives
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   MEDALLION DATA LAKEHOUSE (PostgreSQL 16)            │
├────────────────────────────────────────────────────────────────────────┤
│  raw        │ Raw API JSONB payloads & ingestion execution logs        │
│  staging    │ Type-cast, deduplicated, and validated data tables        │
│  core       │ Canonical daily OHLCV facts (TimescaleDB hypertables)    │
│             │ Security master (dim_security) & calendar dim           │
│  features   │ Versioned 25+ technical & statistical features per date   │
│  ml         │ Model registry, backtests, walk-forward metrics, drift   │
│  app        │ Recommendation snapshots, user portfolio & watchlist     │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               QUANTITATIVE ENGINE & DECISION PIPELINE                  │
├────────────────────────────────────────────────────────────────────────┤
│  • ASPI 200-Day SMA Market Regime Filter (Bullish / Bearish gate)     │
│  • Leak-free LightGBM Model with TimeSeriesSplit Cross-Validation       │
│  • 2.68% CSE Round-Trip Brokerage Fee Hurdle Deduction                 │
│  • 1.5:1 Minimum Risk-to-Reward Ratio Constraint                      │
│  • Minimum LKR 500,000 Average Daily Turnover Liquidity Guardrail      │
│  • Volatility-Adjusted Stop-Loss (1.5 × ATR) & Target Calculation      │
│  • TreeSHAP Feature Attribution & Waterfall Factor Decomposition       │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│             PRESENTATION LAYER (FastAPI + React 18 Dashboard)          │
├────────────────────────────────────────────────────────────────────────┤
│  • Beginner Mode & Pro Quant Mode Toggle                              │
│  • Plain-English & Quantitative SHAP Explainability Modal              │
│  • Interactive Signal Criteria Checklist & Decision Transparent Gates  │
│  • Stock Market 101 Handbook & Viewport-Aware Searchable Glossary      │
│  • Real-Time Portfolio Valuation, Cost Basis & Net Realized/Paper P&L  │
│  • Medallion Database Explorer, CSV Lake Importer & Model Registry     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Current Platform Capabilities

| Metric / Capability | Value / Specification |
|:---|:---|
| **Listed Securities Tracked** | ~291 (All CSE main-board & Diri Savi board equities) |
| **Official CSE Logos** | Synced directly from official CSE Content Delivery Network |
| **Time-Series Storage** | TimescaleDB Hypertables with local Asia/Colombo calendar alignment |
| **Engineered Features** | 25+ leakage-free indicators (RSI, MACD, Bollinger Bands, ATR, Momentum) |
| **Machine Learning Model** | LightGBM Binary Classifier with purged Walk-Forward Validation |
| **Model Explainability** | Per-stock TreeSHAP attribution with plain-English feature descriptions |
| **Decision Gates** | 6-layer quantitative safety filter (Fee hurdle, Regime, Liquidity, R:R, Allocation) |
| **Round-Trip Fee Hurdle** | 2.68% deducted prior to signal generation (broker, SEC, and government levies) |
| **Automated Alerts** | Telegram notification dispatcher with formatted markdown alerts |
| **User Experience** | Pro Quant & Beginner Mode switch, zero-emoji clean SVG UI design |

---

## Quantitative Strategy & Decision Criteria

LankaAlpha AI converts statistical model probabilities into actionable investor signals (**BUY**, **SELL**, **HOLD**, **WATCH**) through six mandatory risk gates:

1. **2.68% Fee Hurdle Rate**: Every trade in Sri Lanka incurs ~1.12% buying fees and ~1.56% selling fees (brokerage commissions, SEC regulatory levies, and government share transaction taxes). The model's expected forward return must exceed **2.68%** after all costs.
2. **ASPI Market Regime Gate**: Evaluates the All Share Price Index against its 200-day Simple Moving Average. In bearish regimes, BUY thresholds are heightened to prevent buying into systemic market downturns.
3. **Probability & Confidence Threshold**: Only stocks where model confidence exceeds **60.0%** are eligible for BUY recommendations.
4. **Risk-to-Reward Ratio (≥ 1.5:1)**: Expected upside to the target price must be at least 1.5 times greater than downside exposure to the stop-loss level.
5. **Liquidity Guardrail**: Requires minimum **LKR 500,000** 30-day average daily turnover to prevent slippage in illiquid counters.
6. **Stop-Loss Protection**: Dynamic stop-loss is placed at **1.5 × ATR (14)** below entry price, and target price is placed at **2.5 × ATR (14)** above entry price.

---

## Project Structure

```
CSE_recommndation/
├── .env.example                     # Environment variable template
├── .gitignore                       # Production gitignore (excludes venv, data, node_modules)
├── alembic.ini                      # Database migration configuration
├── docker-compose.yml               # TimescaleDB PostgreSQL 16 container definition
├── pyproject.toml                   # Python dependencies & packaging specifications
├── README.md                        # Platform documentation
│
├── alembic/                         # Database schema migration versions
│   └── versions/
│       ├── 001_create_raw_layer.py
│       ├── 002_create_staging_layer.py
│       ├── 003_create_core_layer.py       # dim_security, price_daily hypertable
│       ├── 004_create_features_layer.py   # features_daily versioned store
│       ├── 005_create_ml_layer.py         # models, training_runs, predictions
│       └── 006_create_app_layer.py        # recommendations, portfolio, watchlist
│
├── scripts/
│   ├── setup_db.py                  # One-click database bootstrap
│   ├── smoke_test.py                # Live CSE endpoint connectivity check
│   ├── add_logo_column.py           # Database migration helper
│   ├── sync_company_logos.py        # CDN company logo synchronizer
│   └── sync_heavyweights.py         # Top-15 index heavyweights logo bootstrap
│
├── src/
│   ├── config.py                    # Pydantic v2 application settings
│   ├── db.py                        # SQLAlchemy 2.0 engine & session lifecycle
│   ├── main.py                      # Unified CLI entry point
│   │
│   ├── alerts/                      # Broadcast notification modules
│   │   └── telegram.py              # Telegram bot recommendation dispatcher
│   │
│   ├── api/                         # FastAPI REST application
│   │   ├── main.py                  # Route registry & CORS middleware
│   │   └── routes/
│   │       ├── recommendations.py   # Recommendation retrieval & execution
│   │       ├── portfolio.py         # Position management, valuation & watchlist
│   │       ├── models.py            # Model registry, retraining & backtests
│   │       ├── data.py              # Ingestion trigger, lake statistics & CSV import
│   │       ├── db_explorer.py       # Live multi-schema database browser
│   │       └── settings.py          # Trading parameter constraints
│   │
│   ├── core/                        # Data normalizers & master records
│   │   ├── calendar.py              # dim_calendar (Asia/Colombo market days)
│   │   ├── security_master.py       # dim_security master records
│   │   ├── price_daily.py           # Core OHLCV upsert logic
│   │   └── reconciliation.py        # Portfolio price & P&L reconciler
│   │
│   ├── engine/                      # Recommendation & decision logic
│   │   ├── decision.py              # 6-layer quantitative decision gates
│   │   ├── position_sizing.py       # Risk-adjusted position sizing
│   │   └── recommendations.py       # Scored recommendation persistence
│   │
│   ├── features/                    # Feature engineering
│   │   ├── builder.py               # Feature orchestrator
│   │   ├── technical.py             # RSI, MACD, Bollinger, ATR, Volatility
│   │   └── fundamental.py           # Valuation & financial ratios
│   │
│   ├── ingestion/                   # CSE API & data ingestors
│   │   ├── client.py                # HTTP client with retry logic
│   │   ├── endpoints.py             # CSE API URL catalog
│   │   ├── orchestrator.py          # Pipeline execution scheduler
│   │   ├── raw_landing.py           # Raw JSONB lake ingestor
│   │   └── connectors/              # Domain-specific API collectors
│   │
│   ├── models/                      # Machine learning engine
│   │   ├── lgbm_model.py            # LightGBM classifier + TreeSHAP explainability
│   │   ├── registry.py              # Model persistence & champion tracking
│   │   ├── backtester.py            # Walk-forward backtester & performance analytics
│   │   └── regime_filter.py         # ASPI 200-day SMA regime evaluator
│   │
│   ├── staging/                     # Staging transformation
│   │   ├── parser.py                # JSON payload schema parsers
│   │   └── dedup.py                 # Primary key deduplication
│   │
│   └── utils/                       # Shared helper functions
│       ├── time_utils.py            # Colombo timezone calculations
│       └── validation.py            # Input validation routines
│
├── tests/                           # Complete test suite (34 passing tests)
│   ├── test_ai_model.py             # LightGBM, feature normalization, SHAP tests
│   ├── test_api_and_recommendations.py # REST API endpoint assertions
│   ├── test_csv_import.py           # Multi-year historical archive tests
│   ├── test_decision_engine.py      # Quantitative risk gate unit tests
│   └── test_technical_features.py   # Alpha factor mathematical correctness tests
│
└── dashboard/                       # React 18 + Vite frontend
    ├── public/
    │   ├── logo.svg                 # High-resolution vector brand logo
    │   └── favicon.svg              # Browser tab brand icon
    └── src/
        ├── api/client.js            # TanStack Query API hooks
        ├── components/
        │   ├── BeginnerModeContext.jsx # Pro vs Beginner global state
        │   ├── CompanyLogo.jsx      # CDN logo loader with gradient fallback
        │   ├── ExplainabilityModal.jsx # Plain English + SHAP Waterfall modal
        │   ├── InfoTooltip.jsx      # Viewport-aware interactive glossary tooltip
        │   ├── Layout.jsx           # App shell with real-time ASPI indicator
        │   ├── Logo.jsx             # Reusable vector brand component
        │   ├── PortfolioTable.jsx   # Active holdings & closed trades table
        │   ├── PriceChart.jsx       # Recharts interactive OHLCV chart
        │   ├── RecommendationCard.jsx # Actionable signal card
        │   ├── Sidebar.jsx          # High-contrast navigation sidebar
        │   └── SignalCriteriaModal.jsx # Interactive quantitative rules modal
        ├── data/
        │   ├── featureMetadata.js   # Human-friendly descriptions of all 25 features
        │   └── glossary.js          # Financial dictionary with real-world examples
        └── pages/
            ├── Dashboard.jsx        # Real-time overview & top opportunities
            ├── Recommendations.jsx  # Scored signals with multi-criteria filtering
            ├── Portfolio.jsx        # Portfolio valuation, realized P&L & watchlist
            ├── Models.jsx           # Model registry, walk-forward stats & retrain
            ├── DatabaseExplorer.jsx # Interactive lakehouse schema browser
            ├── DataPipeline.jsx     # Automated pipeline run monitor
            ├── DataDownload.jsx     # Multi-period CSE downloader & CSV importer
            ├── StockMarketGuide.jsx # Stock Market 101 guide & searchable glossary
            └── Settings.jsx         # Trading fee & risk threshold preferences
```

---

## Quick Start Guide

### Step 1 — Database Initialization

Start the local TimescaleDB container via Docker:

```powershell
docker compose up -d
```

*(Alternatively, connect to any existing PostgreSQL 16 database with the TimescaleDB extension enabled).*

---

### Step 2 — Backend Setup

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install package and dependencies in editable mode
pip install -e ".[dev]"

# 3. Configure environment variables
Copy-Item .env.example .env
# Edit .env with your database connection credentials if needed

# 4. Bootstrap schemas and run migrations
python -m scripts.setup_db
alembic upgrade head

# 5. Sync CSE company logos
python -m scripts.sync_company_logos
```

---

### Step 3 — Run the Pipeline & Start Services

```powershell
# Download official 1-year price history (Period 5 = 1 Year)
python -m src.main backfill --period 5

# Run daily ingestion, feature calculation & recommendation scoring
python -m src.main daily

# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000
```

---

### Step 4 — Launch the Frontend Dashboard

In a separate terminal:

```powershell
cd dashboard
npm install
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## Frontend Features & Navigation

- **Beginner Mode Switch**: Located in the top header. Toggles beginner-friendly summaries, simplified golden action numbers, and intuitive terminology throughout the entire application.
- **Stock Signals & Recommendations**: Filter by BUY, SELL, HOLD, or WATCH. Every card displays entry range, target profit, stop-loss, and an **Explain** button.
- **Plain-English & SHAP Explainability**: 3-tab modal breaking down recommendations into:
  - *Plain English*: Executive summary and key numbers for beginners.
  - *Quant & SHAP*: Interactive mathematical waterfall decomposing which features pushed the score up or down.
  - *Signal Criteria*: Live audit checklist verifying each of the 6 quantitative safety gates.
- **Portfolio & Risk Monitor**: Track active positions, calculate unrealized paper gains/losses, log exits to capture realized net profits after 2.68% fees, and monitor watchlists with integrated technical charts.
- **Stock Market 101 Handbook & Glossary**: Searchable, categorised educational guide explaining Sri Lankan capital markets, CDS brokerage accounts, P/E ratios, and risk mitigation strategies.
- **Database Explorer**: Direct window into the Medallion Lakehouse (`raw`, `staging`, `core`, `features`, `ml`, `app`) to verify data freshness and table structures without external DB tools.

---

## Testing & Quality Assurance

LankaAlpha AI includes a comprehensive automated test suite verifying feature calculations, LightGBM model stability, leak-free training, API endpoints, and decision logic:

```powershell
.venv\Scripts\activate
pytest tests/ -v
```

```
============================== 34 passed in 8.3s ==============================
```

Build the production frontend bundle:

```powershell
npm --prefix dashboard run build
```

---

## License & Disclaimer

**Disclaimer**: *LankaAlpha AI is an educational and quantitative research platform designed to assist decision-making on the Colombo Stock Exchange (CSE). It does not execute automated trades and does not connect directly to bank accounts or CDS brokerages. All buy and sell orders are placed manually by the user through a licensed stockbroker. Past statistical performance does not guarantee future capital gains. Always practice disciplined risk management.*
