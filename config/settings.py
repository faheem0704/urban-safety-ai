"""
Single source of truth for all configuration.
Loaded from .env at import time. Thresholds are mutable so the
PATCH /api/config/thresholds endpoint can update them in-memory.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # Email / alert credentials
        self.gmail_address:    str = os.getenv("GMAIL_ADDRESS", "")
        self.gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
        self.alert_recipient:  str = os.getenv("ALERT_RECIPIENT", "")

        # Anomaly thresholds (mutable — PATCH /api/config/thresholds can update these)
        self.anomaly_alert_threshold:     float = float(os.getenv("ANOMALY_ALERT_THRESHOLD",     "0.7"))
        self.suspicious_alert_threshold:  float = float(os.getenv("SUSPICIOUS_ALERT_THRESHOLD",  "0.5"))
        self.min_anomaly_frames_to_alert: int   = int(os.getenv("MIN_ANOMALY_FRAMES_TO_ALERT",  "10"))

        # Infrastructure
        self.redis_url:      str  = os.getenv("REDIS_URL",       "redis://localhost:6379/0")
        self.use_fake_redis: bool = os.getenv("USE_FAKE_REDIS",  "true").lower() == "true"


# Module-level singleton — import this everywhere
settings = Settings()
