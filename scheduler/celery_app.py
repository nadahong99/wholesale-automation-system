import logging

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)


def _get_redis_url() -> str:
    try:
        from config.settings import get_settings
        return get_settings().celery_broker_url
    except Exception:
        return "redis://localhost:6379/0"


def _get_result_backend() -> str:
    try:
        from config.settings import get_settings
        return get_settings().celery_result_backend
    except Exception:
        return "redis://localhost:6379/1"


app = Celery(
    "wholesale",
    broker=_get_redis_url(),
    backend=_get_result_backend(),
    include=["scheduler.tasks"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "sourcing_morning": {
            "task": "scheduler.tasks.run_morning_sourcing",
            "schedule": crontab(hour=6, minute=0),
        },
        "price_monitor_morning": {
            "task": "scheduler.tasks.run_price_monitor",
            "schedule": crontab(hour=9, minute=0),
        },
        "sourcing_afternoon": {
            "task": "scheduler.tasks.run_afternoon_sourcing",
            "schedule": crontab(hour=14, minute=0),
        },
        "price_monitor_afternoon": {
            "task": "scheduler.tasks.run_price_monitor",
            "schedule": crontab(hour=16, minute=0),
        },
        "daily_report": {
            "task": "scheduler.tasks.send_daily_report",
            "schedule": crontab(hour=20, minute=0),
        },
        "check_pending_orders": {
            "task": "scheduler.tasks.check_pending_orders",
            "schedule": crontab(minute="*/30"),
        },
        "sync_google_sheets": {
            "task": "scheduler.tasks.sync_google_sheets",
            "schedule": crontab(hour="*/6", minute=0),
        },
    },
)
