"""
Celery Application Configuration
Async task processing for notifications, analytics, etc.
"""
from celery import Celery
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure, task_retry
import logging
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Prometheus metrics for Celery tasks ──────────────────────────────────────
try:
    from prometheus_client import Counter, Histogram, Gauge

    CELERY_TASKS_TOTAL = Counter(
        "celery_tasks_total",
        "Total Celery tasks executed",
        ["task_name", "queue", "state"],
    )
    CELERY_TASK_DURATION = Histogram(
        "celery_task_duration_seconds",
        "Celery task execution duration",
        ["task_name", "queue"],
        buckets=[0.1, 0.5, 1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0],
    )
    CELERY_TASKS_IN_PROGRESS = Gauge(
        "celery_tasks_in_progress",
        "Celery tasks currently running",
        ["task_name"],
    )

    # Task start times keyed by task request id
    _task_start: dict = {}

    @task_prerun.connect
    def on_task_prerun(task_id, task, args, kwargs, **_):
        _task_start[task_id] = time.perf_counter()
        CELERY_TASKS_IN_PROGRESS.labels(task_name=task.name).inc()

    @task_postrun.connect
    def on_task_postrun(task_id, task, args, kwargs, retval, state, **_):
        CELERY_TASKS_IN_PROGRESS.labels(task_name=task.name).dec()
        queue = getattr(task, "queue", "default") or "default"
        CELERY_TASKS_TOTAL.labels(task_name=task.name, queue=queue, state=state).inc()
        start = _task_start.pop(task_id, None)
        if start is not None:
            CELERY_TASK_DURATION.labels(task_name=task.name, queue=queue).observe(
                time.perf_counter() - start
            )

    @task_failure.connect
    def on_task_failure(task_id, exception, traceback, sender, **_):
        queue = getattr(sender, "queue", "default") or "default"
        CELERY_TASKS_TOTAL.labels(task_name=sender.name, queue=queue, state="failure").inc()

    @task_retry.connect
    def on_task_retry(request, reason, einfo, **_):
        CELERY_TASKS_TOTAL.labels(
            task_name=request.task, queue=getattr(request, "delivery_info", {}).get("routing_key", "default"), state="retry"
        ).inc()

except ImportError:
    logger.warning("prometheus_client not available — Celery metrics disabled")

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
    "check-inventory-alerts-hourly": {
        "task": "app.tasks.analytics_tasks.check_inventory_alerts",
        "schedule": crontab(minute=15),  # :15 past every hour
    },
    "update-product-popularity": {
        "task": "app.tasks.analytics_tasks.update_product_popularity",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"
