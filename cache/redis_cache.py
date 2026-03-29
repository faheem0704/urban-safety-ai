"""
CacheManager — Redis-backed cache with fakeredis fallback for development.

  USE_FAKE_REDIS=true  → in-process fakeredis (no Redis server needed)
  USE_FAKE_REDIS=false → real Redis at REDIS_URL

Keys:
  stats:global            TTL 60 s   — cached /api/stats response
  job:summary:{job_id}   TTL 300 s  — cached job summary
"""
import json
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    _STATS_KEY  = "stats:global"
    _STATS_TTL  = 60          # seconds
    _JOB_TTL    = 300         # seconds

    def __init__(self):
        if settings.use_fake_redis:
            import fakeredis
            self._r = fakeredis.FakeRedis(decode_responses=True)
            logger.info("CacheManager: using fakeredis (in-memory)")
        else:
            import redis
            self._r = redis.from_url(settings.redis_url, decode_responses=True)
            logger.info("CacheManager: using Redis at %s", settings.redis_url)

    # ── Stats cache ────────────────────────────────────────────────────

    def cache_stats(self, stats_dict: dict) -> None:
        """Cache the /api/stats response for 60 seconds."""
        try:
            self._r.setex(self._STATS_KEY, self._STATS_TTL, json.dumps(stats_dict))
        except Exception as e:
            logger.warning("cache_stats failed: %s", e)

    def get_cached_stats(self) -> dict | None:
        """Return cached stats or None on miss."""
        try:
            data = self._r.get(self._STATS_KEY)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning("get_cached_stats failed: %s", e)
            return None

    def invalidate_stats(self) -> None:
        """Remove cached stats (call when a new job completes)."""
        try:
            self._r.delete(self._STATS_KEY)
        except Exception as e:
            logger.warning("invalidate_stats failed: %s", e)

    # ── Job summary cache ──────────────────────────────────────────────

    def cache_job_summary(self, job_id: int, summary: dict) -> None:
        """Cache a job summary for 5 minutes."""
        try:
            self._r.setex(f"job:summary:{job_id}", self._JOB_TTL, json.dumps(summary))
        except Exception as e:
            logger.warning("cache_job_summary failed for job %d: %s", job_id, e)

    def get_cached_job_summary(self, job_id: int) -> dict | None:
        """Return cached job summary or None on miss."""
        try:
            data = self._r.get(f"job:summary:{job_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning("get_cached_job_summary failed for job %d: %s", job_id, e)
            return None


# Module-level singleton
cache_manager = CacheManager()
