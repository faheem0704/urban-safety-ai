"""
AlertEngine — sends HTML email alerts via Gmail SMTP (aiosmtplib).

All failures are caught and logged; the main pipeline is never interrupted
by an email error (graceful degradation).
"""
import asyncio
import logging
from datetime import datetime
from email.message import EmailMessage

import aiosmtplib

from alerts.email_templates import (
    ANOMALY_ALERT_SUBJECT,
    ANOMALY_ALERT_TEMPLATE,
    SUMMARY_REPORT_SUBJECT,
    SUMMARY_REPORT_TEMPLATE,
)
from config.settings import settings

logger = logging.getLogger(__name__)


class AlertEngine:
    def __init__(self):
        self._smtp_host = "smtp.gmail.com"
        self._smtp_port = 587

    # ── Public predicates ──────────────────────────────────────────────

    def should_alert(self, anomaly_score: float) -> bool:
        """Return True if the score exceeds the configured anomaly threshold."""
        return anomaly_score >= settings.anomaly_alert_threshold

    # ── Async senders ─────────────────────────────────────────────────

    async def send_anomaly_alert(self, job_id: int, summary_data: dict) -> None:
        """
        Send an anomaly alert email for a completed job.
        Silently skips if anomaly_count < MIN_ANOMALY_FRAMES_TO_ALERT.
        """
        anomaly_count = summary_data.get("anomaly_count", 0)
        if anomaly_count < settings.min_anomaly_frames_to_alert:
            logger.info(
                "Job %d: %d anomaly frames < threshold %d — alert skipped",
                job_id, anomaly_count, settings.min_anomaly_frames_to_alert,
            )
            return

        total    = summary_data.get("total_frames", 1)
        fps      = summary_data.get("fps", 30.0)
        duration = round(total / fps, 1)
        pct      = round(anomaly_count / total * 100, 1) if total else 0.0

        signals_raw = summary_data.get("triggered_signals", [])
        signals_str = "\n".join(f"  • {s}" for s in signals_raw) if signals_raw else "  (none recorded)"

        html = ANOMALY_ALERT_TEMPLATE.substitute(
            job_id            = job_id,
            timestamp_start   = summary_data.get("timestamp_start", 0.0),
            timestamp_end     = summary_data.get("timestamp_end",   duration),
            anomaly_count     = anomaly_count,
            suspicious_count  = summary_data.get("suspicious_count", 0),
            normal_count      = summary_data.get("normal_count",    0),
            total_frames      = total,
            anomaly_pct       = pct,
            triggered_signals = signals_str,
        )
        await self._send(ANOMALY_ALERT_SUBJECT, html)
        logger.info("Anomaly alert sent for job %d (%d anomaly frames)", job_id, anomaly_count)

    async def send_summary_report(self, stats: dict) -> None:
        """Send a daily summary report email."""
        breakdown = stats.get("anomaly_breakdown", {})
        html = SUMMARY_REPORT_TEMPLATE.substitute(
            report_date      = datetime.utcnow().strftime("%Y-%m-%d UTC"),
            total_jobs       = stats.get("total_jobs",   0),
            total_anomalies  = breakdown.get("ANOMALY",  0),
            total_events     = stats.get("total_events", 0),
            count_anomaly    = breakdown.get("ANOMALY",    0),
            count_suspicious = breakdown.get("SUSPICIOUS", 0),
            count_normal     = breakdown.get("NORMAL",     0),
            busiest_hour     = stats.get("busiest_hour", "N/A"),
        )
        await self._send(SUMMARY_REPORT_SUBJECT, html)
        logger.info("Daily summary report sent")

    # ── Sync wrappers (for Celery tasks) ─────────────────────────────

    def send_anomaly_alert_sync(self, job_id: int, summary_data: dict) -> None:
        """Synchronous wrapper — safe to call from Celery task threads."""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.send_anomaly_alert(job_id, summary_data))
        except Exception as e:
            logger.error("send_anomaly_alert_sync failed for job %d: %s", job_id, e)
        finally:
            loop.close()

    def send_summary_report_sync(self, stats: dict) -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.send_summary_report(stats))
        except Exception as e:
            logger.error("send_summary_report_sync failed: %s", e)
        finally:
            loop.close()

    # ── Internal SMTP helper ──────────────────────────────────────────

    async def _send(self, subject: str, html_body: str) -> None:
        """Send an HTML email via Gmail SMTP. Raises on failure (caller catches)."""
        if not settings.gmail_address or "placeholder" in settings.gmail_address:
            logger.warning("Email credentials not configured — skipping send (subject: %s)", subject)
            return

        msg = EmailMessage()
        msg["From"]    = settings.gmail_address
        msg["To"]      = settings.alert_recipient
        msg["Subject"] = subject
        msg.set_content(html_body, subtype="html")

        try:
            await aiosmtplib.send(
                msg,
                hostname  = self._smtp_host,
                port      = self._smtp_port,
                username  = settings.gmail_address,
                password  = settings.gmail_app_password,
                start_tls = True,
            )
        except Exception as e:
            # Graceful failure: log but never crash the pipeline
            logger.error("SMTP send failed (subject='%s'): %s", subject, e)
