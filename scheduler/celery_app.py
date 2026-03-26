# scheduler/celery_app.py
"""Celery application configuration."""
from celery import Celery
from celery.schedules import crontab
from config.settings import settings

celery_app = Celery(
    "wholesale",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["scheduler.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Beat schedule ─────────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "auto-sourcing-morning": {
        "task": "scheduler.tasks.auto_sourcing",
        "schedule": crontab(hour=6, minute=0),  # 06:00 KST
    },
    "golden-keyword-filter": {
        "task": "scheduler.tasks.golden_keyword_filter",
        "schedule": crontab(hour=9, minute=0),  # 09:00 KST
    },
    "auto-sourcing-afternoon": {
        "task": "scheduler.tasks.auto_sourcing",
        "schedule": crontab(hour=14, minute=0),  # 14:00 KST
    },
    "price-monitor-afternoon": {
        "task": "scheduler.tasks.price_monitoring",
        "schedule": crontab(hour=16, minute=0),  # 16:00 KST
    },
    "daily-report": {
        "task": "scheduler.tasks.daily_report",
        "schedule": crontab(hour=20, minute=0),  # 20:00 KST
    },
    "hourly-price-check": {
        "task": "scheduler.tasks.price_monitoring",
        "schedule": crontab(minute=0),  # every hour
    },
}
