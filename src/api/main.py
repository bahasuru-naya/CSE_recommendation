"""FastAPI main application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import data, models, portfolio, recommendations, settings, db_explorer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup/shutdown tasks."""
    logger.info("CSE Recommendation API started.")
    yield
    logger.info("CSE Recommendation API shutting down.")


app = FastAPI(
    title="CSE Stock Recommendation Engine API",
    description="Automated stock recommendation and lakehouse system for the Colombo Stock Exchange",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React dashboard (Vite default :5173 and standard :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(db_explorer.router, prefix="/api/db", tags=["db-explorer"])


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "cse_recommendation_api", "timestamp": datetime.utcnow().isoformat()}
