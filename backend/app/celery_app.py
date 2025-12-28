"""
Celery Application Configuration
Async task processing for notifications, analytics, etc.
"""
from celery import Celery
from celery.schedules import crontab
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "ecommerce_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.sync_tasks",
        "app.tasks.order_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    task_queues={
        "sync_queue": {
            "exchange": "sync",
            "routing_key": "sync",
        },
        "order_queue": {
            "exchange": "orders",
            "routing_key": "orders",
        },
        "analytics_queue": {
            "exchange": "analytics",
            "routing_key": "analytics",
        },
        "notifications_queue": {
            "exchange": "notifications",
            "routing_key": "notifications",
        },
    },
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "evaluate-store-tiers-every-hour": {
        "task": "app.tasks.sync_tasks.evaluate_all_store_tiers",
        "schedule": crontab(minute=0),  # Every hour
    },
    "cleanup-old-sync-logs": {
        "task": "app.tasks.sync_tasks.cleanup_old_sync_logs",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "generate-daily-analytics": {
        "task": "app.tasks.analytics_tasks.generate_daily_analytics",
        "schedule": crontab(hour=1, minute=0),  # 1 AM daily
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"
