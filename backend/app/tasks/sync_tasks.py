"""
Sync-related Celery tasks
"""
from celery import Task
from datetime import datetime, timedelta
import logging

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.models import Store, SyncLog, StoreTier
from app.services.sync_engine import TierManager

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.sync_tasks.evaluate_all_store_tiers")
def evaluate_all_store_tiers(self):
    """
    Periodic task to evaluate and adjust store tiers
    Runs every hour
    """
    logger.info("Starting store tier evaluation...")
    
    stores = self.db.query(Store).filter(Store.is_active == True).all()
    tier_manager = TierManager(self.db)
    
    updated_count = 0
    for store in stores:
        try:
            old_tier = store.sync_tier
            tier_manager.evaluate_and_adjust_tier(store.id)
            
            if store.sync_tier != old_tier:
                updated_count += 1
                logger.info(f"Store {store.name} tier updated: {old_tier} → {store.sync_tier}")
        except Exception as e:
            logger.error(f"Failed to evaluate tier for store {store.id}: {e}")
    
    logger.info(f"Tier evaluation complete. {updated_count} stores updated.")
    return {"evaluated": len(stores), "updated": updated_count}


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.sync_tasks.cleanup_old_sync_logs")
def cleanup_old_sync_logs(self):
    """
    Clean up sync logs older than 30 days
    Runs daily at 2 AM
    """
    logger.info("Starting sync log cleanup...")
    
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    deleted = self.db.query(SyncLog).filter(
        SyncLog.started_at < cutoff_date
    ).delete()
    
    self.db.commit()
    
    logger.info(f"Deleted {deleted} old sync logs")
    return {"deleted": deleted}


@celery_app.task(name="app.tasks.sync_tasks.process_sync_webhook")
def process_sync_webhook(store_id: str, webhook_data: dict):
    """
    Process real-time sync webhooks from billing systems
    High priority task
    """
    logger.info(f"Processing sync webhook for store {store_id}")
    
    # Implementation would process webhook data
    # Update inventory in real-time
    # Trigger cache invalidation
    
    return {"success": True, "store_id": store_id}
