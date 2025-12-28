"""
Sync API Endpoints
Handles product/inventory synchronization from billing systems
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.schemas.schemas import SyncBatchRequest, SyncBatchResponse, APIResponse
from app.services.sync_engine import SyncEngine, TierManager
from app.models.models import Store

logger = logging.getLogger(__name__)

router = APIRouter()


async def verify_sync_api_key(
    x_api_key: str = Header(..., description="Sync API Key"),
    db: Session = Depends(get_db)
) -> Store:
    """Verify sync API key and return store"""
    store = db.query(Store).filter(Store.sync_api_key == x_api_key).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    if not store.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store is not active"
        )
    return store


@router.post("/products/batch", response_model=APIResponse)
async def sync_products_batch(
    request: SyncBatchRequest,
    store: Store = Depends(verify_sync_api_key),
    db: Session = Depends(get_db)
):
    """
    Batch product synchronization endpoint
    
    - **sync_type**: 'delta' (only changed), 'full' (all products), 'inventory_only' (quantities only)
    - **products**: List of products (max 1000 per batch)
    - Supports idempotent operations via checksum
    - Returns detailed sync results
    """
    try:
        # Verify store matches request
        if str(store.id) != str(request.store_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not match store_id"
            )
        
        # Process sync
        sync_engine = SyncEngine(db)
        result = await sync_engine.process_batch_sync(
            store_id=request.store_id,
            sync_type=request.sync_type,
            products=request.products
        )
        
        # Adjust tier based on activity
        tier_manager = TierManager(db)
        await tier_manager.evaluate_and_adjust_tier(request.store_id)
        
        logger.info(
            f"Sync completed for store {store.name}: "
            f"{result.created} created, {result.updated} updated, {result.failed} failed"
        )
        
        return APIResponse(
            success=True,
            data=result.dict(),
            meta={
                "store_id": str(store.id),
                "store_name": store.name,
                "sync_tier": store.sync_tier
            }
        )
        
    except ValueError as e:
        logger.error(f"Sync validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync operation failed"
        )


@router.get("/status", response_model=APIResponse)
async def get_sync_status(
    store: Store = Depends(verify_sync_api_key),
    db: Session = Depends(get_db)
):
    """
    Get sync status and recommendations for a store
    
    Returns:
    - Last sync timestamp
    - Sync tier
    - Recommended sync interval
    - Next recommended sync time
    """
    from app.models.models import SyncLog
    from sqlalchemy import desc
    
    # Get latest sync log
    last_sync = db.query(SyncLog).filter(
        SyncLog.store_id == store.id
    ).order_by(desc(SyncLog.started_at)).first()
    
    return APIResponse(
        success=True,
        data={
            "store_id": str(store.id),
            "store_name": store.name,
            "sync_tier": store.sync_tier,
            "sync_interval_minutes": store.sync_interval_minutes,
            "last_sync_at": store.last_sync_at,
            "last_sync_status": last_sync.status if last_sync else None,
            "last_sync_duration": last_sync.duration_seconds if last_sync else None,
            "recommended_next_sync": None  # Calculate based on tier
        }
    )


@router.get("/logs", response_model=APIResponse)
async def get_sync_logs(
    limit: int = 20,
    store: Store = Depends(verify_sync_api_key),
    db: Session = Depends(get_db)
):
    """Get recent sync logs for a store"""
    from app.models.models import SyncLog
    from sqlalchemy import desc
    
    logs = db.query(SyncLog).filter(
        SyncLog.store_id == store.id
    ).order_by(desc(SyncLog.started_at)).limit(limit).all()
    
    return APIResponse(
        success=True,
        data=[
            {
                "sync_id": str(log.id),
                "sync_type": log.sync_type,
                "status": log.status,
                "records_received": log.records_received,
                "records_created": log.records_created,
                "records_updated": log.records_updated,
                "records_failed": log.records_failed,
                "duration_seconds": log.duration_seconds,
                "started_at": log.started_at,
                "completed_at": log.completed_at
            }
            for log in logs
        ],
        meta={"total": len(logs)}
    )
