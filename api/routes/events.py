from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.schemas import EventResponse
from cache.redis_cache import cache_manager
from database.database import get_db
from database.models import AnalysisJob, AnomalyEvent

router = APIRouter()


@router.get("/events", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db)):
    """Return the 50 most recent anomaly events across all jobs."""
    return (
        db.query(AnomalyEvent)
        .order_by(AnomalyEvent.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Return a single event by ID."""
    event = db.query(AnomalyEvent).filter(AnomalyEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Aggregate statistics across all jobs.
    Response is cached in Redis/fakeredis for 60 seconds.
    Cache is invalidated automatically when a new job completes.
    """
    # ── Cache hit ────────────────────────────────────────────────────
    cached = cache_manager.get_cached_stats()
    if cached is not None:
        return {**cached, "_cached": True}

    # ── Cache miss: compute from DB ──────────────────────────────────
    total_jobs   = db.query(func.count(AnalysisJob.id)).scalar()  or 0
    total_events = db.query(func.count(AnomalyEvent.id)).scalar() or 0

    breakdown_rows = (
        db.query(AnomalyEvent.classification, func.count(AnomalyEvent.id))
        .group_by(AnomalyEvent.classification)
        .all()
    )
    anomaly_breakdown = {cls: cnt for cls, cnt in breakdown_rows}

    busiest_row = (
        db.query(
            func.strftime("%H", AnomalyEvent.created_at).label("hour"),
            func.count(AnomalyEvent.id).label("count"),
        )
        .group_by("hour")
        .order_by(func.count(AnomalyEvent.id).desc())
        .first()
    )

    stats = {
        "total_jobs":        total_jobs,
        "total_events":      total_events,
        "anomaly_breakdown": anomaly_breakdown,
        "busiest_hour":      busiest_row.hour if busiest_row else None,
    }

    # ── Store in cache ───────────────────────────────────────────────
    cache_manager.cache_stats(stats)
    return {**stats, "_cached": False}
