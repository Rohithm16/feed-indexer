"""
FastAPI application entry point.

Startup sequence:
1. Create DB tables (if they don't exist)
2. Register API routers
3. Start background scheduler (which triggers an immediate ingestion)

Run with: uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.api import events, feeds, prefs
from app.ingestion.pipeline import run_ingestion




# Basic logging config — shows timestamps and log levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Initializing database tables...")
    init_db()

    logger.info("Starting background scheduler...")
    await start_scheduler()

    yield  # App is now running

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down scheduler...")
    stop_scheduler()


app = FastAPI(
    title="Feed Indexer",
    description="AI-powered news aggregator that clusters articles into events",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the frontend (served on any port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── Register routers ─────────────────────────────────────────────────────────
app.include_router(events.router)
app.include_router(feeds.router)
app.include_router(prefs.router)


@app.head("/")
@app.get("/")
def read_root():
    """Root endpoint to handle UptimeRobot HEAD requests and keep the server awake."""
    return {"status": "alive"}


@app.get("/api/health")
def health():
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/api/ingest")
async def trigger_ingestion():
    """
    Manually trigger a full ingestion run.
    Useful for testing or forcing a refresh.
    """
    result = await run_ingestion()
    return result
