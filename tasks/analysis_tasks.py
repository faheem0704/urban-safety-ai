"""
Celery tasks for video analysis.

process_video_task(job_id, video_path):
  1. Sets job status → "processing"
  2. Runs YOLO detection
  3. Runs two-layer anomaly pipeline (SafetyMonitor)
  4. Persists all AnomalyEvent records to DB
  5. Sets job status → "complete" with frame counts
  6. Invalidates the stats cache
  7. Sends anomaly alert email (graceful failure)
  8. Broadcasts ANOMALY frames over WebSocket

WebSocket broadcast uses asyncio.run_coroutine_threadsafe() so it can be
called from a Celery worker thread without creating a new event loop.
"""
import asyncio
import json
import logging
from datetime import datetime

from tasks.celery_app import celery_app
from database.database import SessionLocal
from database.models import AnalysisJob, AnomalyEvent

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.process_video")
def process_video_task(self, job_id: int, video_path: str) -> dict:
    """Full video analysis pipeline as a Celery task."""
    db = SessionLocal()
    try:
        # ── 1. Mark processing ────────────────────────────────────────
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        job.status = "processing"
        db.commit()
        logger.info("Job %d: started processing %s", job_id, video_path)

        # ── 2. YOLO detection ─────────────────────────────────────────
        from ai_core.detector import VideoDetector
        detection_results = VideoDetector().process(video_path)

        # ── 3. Two-layer anomaly pipeline ─────────────────────────────
        from ai_core.combined_detector import SafetyMonitor
        results = SafetyMonitor().process_detections(detection_results)

        fps    = results["fps"]
        counts = {"NORMAL": 0, "SUSPICIOUS": 0, "ANOMALY": 0}
        all_signals: list[str] = []

        # ── 4. Persist events & broadcast ─────────────────────────────
        for frame_data in results["frames"]:
            cls   = frame_data["final_classification"]
            score = frame_data["rule_based"]["score"]
            sigs  = frame_data["rule_based"]["triggered_signals"]
            ts    = round(frame_data["frame"] / fps, 3)

            counts[cls] = counts.get(cls, 0) + 1
            if sigs:
                all_signals.extend(sigs)

            db.add(AnomalyEvent(
                job_id            = job_id,
                frame_number      = frame_data["frame"],
                timestamp_sec     = ts,
                classification    = cls,
                anomaly_score     = score,
                triggered_signals = json.dumps(sigs),
            ))

            if cls == "ANOMALY":
                _ws_broadcast({
                    "type":      "anomaly_alert",
                    "frame":     frame_data["frame"],
                    "timestamp": ts,
                    "score":     score,
                    "signals":   sigs,
                })

        db.commit()

        # ── 5. Mark complete ──────────────────────────────────────────
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        job.status            = "complete"
        job.completed_at      = datetime.utcnow()
        job.total_frames      = results["total_frames"]
        job.normal_frames     = counts["NORMAL"]
        job.suspicious_frames = counts["SUSPICIOUS"]
        job.anomaly_frames    = counts["ANOMALY"]
        job.fps               = fps
        db.commit()
        logger.info("Job %d: complete — %s", job_id, counts)

        # ── 6. Invalidate stats cache ─────────────────────────────────
        try:
            from cache.redis_cache import cache_manager
            cache_manager.invalidate_stats()
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)

        # ── 7. Send email alert (graceful failure) ────────────────────
        unique_signals = list(dict.fromkeys(all_signals))  # deduplicated, ordered
        summary_data = {
            "job_id":           job_id,
            "anomaly_count":    counts["ANOMALY"],
            "suspicious_count": counts["SUSPICIOUS"],
            "normal_count":     counts["NORMAL"],
            "total_frames":     results["total_frames"],
            "fps":              fps,
            "triggered_signals": unique_signals,
            "timestamp_start":  0.0,
            "timestamp_end":    round(results["total_frames"] / fps, 1),
        }
        _send_alert(job_id, summary_data)

        return {"job_id": job_id, "status": "complete", "anomaly_frames": counts["ANOMALY"]}

    except Exception as exc:
        logger.error("Job %d failed: %s", job_id, exc, exc_info=True)
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


# ── Helpers ────────────────────────────────────────────────────────────────

def _ws_broadcast(message: dict) -> None:
    """
    Broadcast a WebSocket message from a Celery worker thread.
    Uses run_coroutine_threadsafe to schedule on the main FastAPI event loop.
    Silently drops if no loop is available (e.g., during tests).
    """
    try:
        import main as _main
        from api.websocket import manager
        loop: asyncio.AbstractEventLoop | None = getattr(_main, "_main_event_loop", None)
        if loop and loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(manager.broadcast(message), loop)
            fut.result(timeout=2)
    except Exception as e:
        logger.debug("WS broadcast skipped: %s", e)


def _send_alert(job_id: int, summary_data: dict) -> None:
    """Send anomaly alert email synchronously. Never raises."""
    try:
        from alerts.alert_engine import AlertEngine
        AlertEngine().send_anomaly_alert_sync(job_id, summary_data)
    except Exception as e:
        logger.error("Alert dispatch failed for job %d: %s", job_id, e)
