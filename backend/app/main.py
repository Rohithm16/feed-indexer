"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, events, feeds, prefs
from app.database import init_db
from app.ingestion.pipeline import run_ingestion
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    init_db()

    logger.info("Starting background scheduler...")
    await start_scheduler()

    yield

    logger.info("Shutting down scheduler...")
    stop_scheduler()


app = FastAPI(
    title="Feed Indexer",
    description="AI-powered news aggregator that clusters articles into events",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ["http://localhost:5173", "http://127.0.0.1:5173"] if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(events.router)
app.include_router(feeds.router)
app.include_router(prefs.router)
app.include_router(auth.router)


@app.head("/")
@app.get("/")
def read_root():
    return {"status": "alive"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ingest")
async def trigger_ingestion():
    return await run_ingestion()
