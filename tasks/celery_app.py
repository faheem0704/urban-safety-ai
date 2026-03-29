"""
Celery application factory.

Dev mode  (USE_FAKE_REDIS=true):
    broker  = memory://   (in-process, no Redis server needed)
    backend = cache+memory://
    task_always_eager = True  → tasks run synchronously when .delay() is called;
                                analysis.py wraps the call in a daemon thread so
                                the API response is returned immediately.

Prod mode (USE_FAKE_REDIS=false):
    broker  = Redis URL from .env
    backend = Redis URL from .env
    Requires a Celery worker: celery -A tasks.celery_app worker --loglevel=info
"""
from config.settings import settings
from celery import Celery

if settings.use_fake_redis:
    _broker  = "memory://"
    _backend = "cache+memory://"
else:
    _broker  = settings.redis_url
    _backend = settings.redis_url

celery_app = Celery(
    "urban_safety",
    broker  = _broker,
    backend = _backend,
    include = ["tasks.analysis_tasks"],
)

celery_app.conf.update(
    task_serializer    = "json",
    result_serializer  = "json",
    accept_content     = ["json"],
    task_always_eager  = settings.use_fake_redis,  # dev: run synchronously in-thread
    task_eager_propagates = True,                  # surface exceptions immediately
    task_track_started = True,
)
