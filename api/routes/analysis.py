import os
import shutil
import threading
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from api.schemas import AnalysisSummary, AnomalyTimestamp, EventResponse, JobResponse
from config.settings import settings
from database.database import SessionLocal, get_db
from database.models import AnalysisJob, AnomalyEvent

router = APIRouter()


# ── Upload & dispatch ────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a video file and enqueue it for analysis.

    Returns job_id immediately. Poll GET /api/jobs/{job_id} for status.

    Dev mode  (USE_FAKE_REDIS=true):  Celery task runs in a daemon thread
                                       (no separate worker needed).
    Prod mode (USE_FAKE_REDIS=false): Task is sent to Redis; requires a
                                       running Celery worker.
    """
    os.makedirs("temp", exist_ok=True)

    job = AnalysisJob(filename=file.filename, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    video_path = f"temp/{job.id}_{file.filename}"
    with open(video_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    _dispatch_task(job.id, video_path)

    return {
        "job_id":   job.id,
        "status":   "pending",
        "message":  f"Processing started. Poll /api/jobs/{job.id} for updates.",
    }


def _dispatch_task(job_id: int, video_path: str) -> None:
    """
    Dispatch process_video_task to Celery.

    When task_always_eager=True (dev/fakeredis mode), .delay() runs the task
    synchronously in the calling thread. We wrap it in a daemon thread so the
    API endpoint returns immediately without blocking on the full pipeline.
    """
    from tasks.analysis_tasks import process_video_task

    if settings.use_fake_redis:
        # Run the eager (synchronous) task in a background thread
        t = threading.Thread(
            target=process_video_task.delay,
            args=(job_id, video_path),
            daemon=True,
        )
        t.start()
    else:
        # Real Redis broker: enqueue and a Celery worker picks it up
        process_video_task.delay(job_id, video_path)


# ── Job status & summary ────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Return job status and, once complete, an analysis summary."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    summary = None
    if job.status == "complete":
        summary = _build_summary(job_id, job, db)

    return {"job": JobResponse.model_validate(job), "summary": summary}


@router.get("/jobs/{job_id}/events", response_model=list[EventResponse])
def get_job_events(
    job_id: int,
    classification: Optional[str] = Query(None, description="Filter: NORMAL / SUSPICIOUS / ANOMALY"),
    db: Session = Depends(get_db),
):
    """Return all events for a job, optionally filtered by classification."""
    if not db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first():
        raise HTTPException(status_code=404, detail="Job not found")

    q = db.query(AnomalyEvent).filter(AnomalyEvent.job_id == job_id)
    if classification:
        q = q.filter(AnomalyEvent.classification == classification.upper())
    return q.order_by(AnomalyEvent.frame_number).all()


# ── Helpers ─────────────────────────────────────────────────────────────────

def _build_summary(job_id: int, job: AnalysisJob, db: Session) -> AnalysisSummary:
    fps          = job.fps or 30.0
    total        = job.total_frames or 0
    duration_sec = round(total / fps, 2)

    anomaly_events = (
        db.query(AnomalyEvent)
        .filter(AnomalyEvent.job_id == job_id, AnomalyEvent.classification == "ANOMALY")
        .order_by(AnomalyEvent.timestamp_sec)
        .all()
    )
    timestamps = _group_timestamps([e.timestamp_sec for e in anomaly_events], gap=1.0)

    anomaly_count    = job.anomaly_frames    or 0
    suspicious_count = job.suspicious_frames or 0
    normal_count     = job.normal_frames     or 0
    pct              = round(anomaly_count / total * 100, 2) if total else 0.0

    return AnalysisSummary(
        job_id             = job_id,
        duration_sec       = duration_sec,
        normal_count       = normal_count,
        suspicious_count   = suspicious_count,
        anomaly_count      = anomaly_count,
        anomaly_percentage = pct,
        anomaly_timestamps = [AnomalyTimestamp(start=s, end=e) for s, e in timestamps],
    )


def _group_timestamps(timestamps: list[float], gap: float = 1.0) -> list[tuple[float, float]]:
    if not timestamps:
        return []
    groups: list[tuple[float, float]] = []
    start = prev = timestamps[0]
    for ts in timestamps[1:]:
        if ts - prev > gap:
            groups.append((start, prev))
            start = ts
        prev = ts
    groups.append((start, prev))
    return groups
