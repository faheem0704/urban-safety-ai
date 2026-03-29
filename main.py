import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.routes import analysis, events
from api.websocket import router as ws_router
from cache.redis_cache import cache_manager  # noqa: F401 — initialised on import
from config.settings import settings
from database.database import init_db

logger = logging.getLogger(__name__)

# Captured at startup so Celery worker threads can schedule WS broadcasts
# on the correct event loop via asyncio.run_coroutine_threadsafe().
_main_event_loop: Optional[asyncio.AbstractEventLoop] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_event_loop
    _main_event_loop = asyncio.get_event_loop()

    init_db()

    print("=" * 52)
    print("  Urban Safety AI  —  server ready")
    print(f"  Docs      : http://localhost:8000/docs")
    print(f"  WS        : ws://localhost:8000/ws/live")
    print(f"  Cache     : {'fakeredis (dev)' if settings.use_fake_redis else settings.redis_url}")
    print(f"  Celery    : {'eager/thread (dev)' if settings.use_fake_redis else 'Redis broker'}")
    print("=" * 52)
    yield
    # Shutdown — nothing to tear down for SQLite / fakeredis


app = FastAPI(
    title       = "Urban Safety AI",
    version     = "1.0.0",
    description = "AI-powered urban safety monitoring — two-layer anomaly detection + async task queue.",
    docs_url    = "/docs",
    lifespan    = lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(events.router,   prefix="/api", tags=["Events"])
app.include_router(ws_router,                      tags=["WebSocket"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "model": "loaded", "version": "1.0.0"}


# ── Config endpoints ──────────────────────────────────────────────────────────
@app.get("/api/config", tags=["Config"])
def get_config():
    """Return current threshold settings (no credentials exposed)."""
    return {
        "anomaly_alert_threshold":     settings.anomaly_alert_threshold,
        "suspicious_alert_threshold":  settings.suspicious_alert_threshold,
        "min_anomaly_frames_to_alert": settings.min_anomaly_frames_to_alert,
        "use_fake_redis":              settings.use_fake_redis,
        "redis_url":                   settings.redis_url if not settings.use_fake_redis else "fakeredis",
    }


class ThresholdUpdate(BaseModel):
    anomaly_threshold:    Optional[float] = None
    suspicious_threshold: Optional[float] = None
    min_anomaly_frames:   Optional[int]   = None


@app.patch("/api/config/thresholds", tags=["Config"])
def update_thresholds(body: ThresholdUpdate):
    """
    Update anomaly detection thresholds in-memory.
    Changes take effect immediately for new jobs; no server restart needed.
    """
    if body.anomaly_threshold is not None:
        settings.anomaly_alert_threshold = body.anomaly_threshold
    if body.suspicious_threshold is not None:
        settings.suspicious_alert_threshold = body.suspicious_threshold
    if body.min_anomaly_frames is not None:
        settings.min_anomaly_frames_to_alert = body.min_anomaly_frames

    return {
        "updated": True,
        "anomaly_alert_threshold":     settings.anomaly_alert_threshold,
        "suspicious_alert_threshold":  settings.suspicious_alert_threshold,
        "min_anomaly_frames_to_alert": settings.min_anomaly_frames_to_alert,
    }
