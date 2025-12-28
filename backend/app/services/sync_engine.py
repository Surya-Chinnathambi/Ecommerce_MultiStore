"""
Intelligent Sync Engine
Implements tier-based adaptive synchronization with conflict resolution
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import logging
from uuid import UUID, uuid4

from app.models.models import Product, Store, SyncLog, StoreTier
from app.schemas.schemas import SyncProductItem, SyncBatchResponse
from app.core.redis import redis_client, CacheKeys
from app.core.config import settings

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Intelligent sync engine with tier-based optimization
    Implements delta sync, conflict resolution, and bandwidth optimization
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_batch_sync(
        self,
        store_id: UUID,
        sync_type: str,
        products: List[SyncProductItem]
    ) -> SyncBatchResponse:
        """
        Process batch product synchronization
        
        Args:
            store_id: Store UUID
            sync_type: 'delta', 'full', or 'inventory_only'
            products: List of product updates
        
        Returns:
            SyncBatchResponse with results
        """
        start_time = datetime.utcnow()
        sync_id = uuid4()
        
        # Initialize counters
        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        # Get store
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise ValueError("Store not found")
        
        # Process products
        for product_data in products:
            try:
                if sync_type == "inventory_only":
                    success = await self._update_inventory_only(store_id, product_data)
                else:
                    success = await self._upsert_product(store_id, product_data, sync_type)
                
                if success == "created":
                    stats["created"] += 1
                elif success == "updated":
                    stats["updated"] += 1
                
                stats["processed"] += 1
                
            except Exception as e:
                logger.error(f"Failed to sync product {product_data.external_id}: {e}")
                stats["failed"] += 1
                stats["errors"].append({
                    "external_id": product_data.external_id,
                    "error": str(e)
                })
        
        # Update store last_sync_at
        store.last_sync_at = datetime.utcnow()
        self.db.commit()
        
        # Invalidate cache
        await self._invalidate_store_cache(store_id)
        
        # Log sync operation
        duration = (datetime.utcnow() - start_time).total_seconds()
        await self._log_sync(store_id, sync_id, sync_type, stats, duration)
        
        # Calculate next sync time based on tier
        next_sync_at = self._calculate_next_sync_time(store.sync_tier)
        
        return SyncBatchResponse(
            success=stats["failed"] == 0,
            sync_id=sync_id,
            processed=stats["processed"],
            created=stats["created"],
            updated=stats["updated"],
            failed=stats["failed"],
            errors=stats["errors"],
            next_sync_recommended_at=next_sync_at,
            duration_seconds=duration
        )
    
    async def _upsert_product(
        self,
        store_id: UUID,
        product_data: SyncProductItem,
        sync_type: str
    ) -> str:
        """
        Insert or update product with conflict resolution
        Returns: 'created' or 'updated'
        """
        # Check if product exists
        existing_product = self.db.query(Product).filter(
            and_(
                Product.store_id == store_id,
                Product.external_id == product_data.external_id
            )
        ).first()
        
        # Calculate checksum for change detection
        checksum = self._calculate_checksum(product_data)
        
        if existing_product:
            # Update only if changed
            if sync_type == "delta" and existing_product.sync_checksum == checksum:
                logger.debug(f"Product {product_data.external_id} unchanged, skipping")
                return "updated"
            
            # Update product
            self._update_product_fields(existing_product, product_data)
            existing_product.sync_checksum = checksum
            existing_product.sync_version += 1
            existing_product.last_synced_at = datetime.utcnow()
            existing_product.updated_at = datetime.utcnow()
            
            # Update stock status
            existing_product.is_in_stock = existing_product.quantity > 0
            
            self.db.commit()
            logger.info(f"Updated product {product_data.external_id}")
            return "updated"
        else:
            # Create new product
            new_product = Product(
                id=uuid4(),
                store_id=store_id,
                external_id=product_data.external_id,
                name=product_data.name,
                slug=self._generate_slug(product_data.name),
                description=product_data.description,
                mrp=product_data.mrp,
                selling_price=product_data.selling_price,
                quantity=product_data.quantity,
                unit=product_data.unit,
                sku=product_data.sku,
                barcode=product_data.barcode,
                hsn_code=product_data.hsn_code,
                gst_percent=product_data.gst_percent or 0,
                is_active=True,
                is_in_stock=product_data.quantity > 0,
                sync_checksum=checksum,
                sync_version=1,
                last_synced_at=datetime.utcnow(),
                discount_percent=self._calculate_discount(product_data.mrp, product_data.selling_price)
            )
            
            self.db.add(new_product)
            self.db.commit()
            logger.info(f"Created product {product_data.external_id}")
            return "created"
    
    async def _update_inventory_only(
        self,
        store_id: UUID,
        product_data: SyncProductItem
    ) -> str:
        """
        Update only inventory quantity (faster for frequent updates)
        """
        product = self.db.query(Product).filter(
            and_(
                Product.store_id == store_id,
                Product.external_id == product_data.external_id
            )
        ).first()
        
        if product:
            product.quantity = product_data.quantity
            product.is_in_stock = product_data.quantity > 0
            product.last_synced_at = datetime.utcnow()
            product.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Invalidate inventory cache
            cache_key = CacheKeys.inventory(str(store_id), str(product.id))
            await redis_client.delete(cache_key)
            
            return "updated"
        else:
            # Product doesn't exist, create it
            return await self._upsert_product(store_id, product_data, "full")
    
    def _update_product_fields(self, product: Product, data: SyncProductItem):
        """Update product fields from sync data"""
        product.name = data.name
        product.description = data.description
        product.mrp = data.mrp
        product.selling_price = data.selling_price
        product.quantity = data.quantity
        product.unit = data.unit
        product.sku = data.sku
        product.barcode = data.barcode
        product.hsn_code = data.hsn_code
        product.gst_percent = data.gst_percent or 0
        product.discount_percent = self._calculate_discount(data.mrp, data.selling_price)
    
    def _calculate_checksum(self, product_data: SyncProductItem) -> str:
        """Generate MD5 checksum for change detection"""
        data_str = f"{product_data.name}|{product_data.mrp}|{product_data.selling_price}|{product_data.quantity}"
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _calculate_discount(self, mrp: float, selling_price: float) -> float:
        """Calculate discount percentage"""
        if mrp > 0:
            return round(((mrp - selling_price) / mrp) * 100, 2)
        return 0.0
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from product name"""
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug.strip('-')[:500]
    
    async def _invalidate_store_cache(self, store_id: UUID):
        """Invalidate all product caches for store"""
        pattern = f"store:{str(store_id)}:product*"
        await redis_client.delete_pattern(pattern)
        logger.debug(f"Invalidated cache for store {store_id}")
    
    async def _log_sync(
        self,
        store_id: UUID,
        sync_id: UUID,
        sync_type: str,
        stats: Dict[str, Any],
        duration: float
    ):
        """Log sync operation for monitoring"""
        sync_log = SyncLog(
            id=sync_id,
            store_id=store_id,
            sync_type=sync_type,
            status="success" if stats["failed"] == 0 else "partial" if stats["processed"] > 0 else "failed",
            records_received=stats["processed"] + stats["failed"],
            records_created=stats["created"],
            records_updated=stats["updated"],
            records_failed=stats["failed"],
            duration_seconds=duration,
            error_details=stats["errors"] if stats["errors"] else None,
            started_at=datetime.utcnow() - timedelta(seconds=duration),
            completed_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
    
    def _calculate_next_sync_time(self, tier: StoreTier) -> datetime:
        """Calculate recommended next sync time based on store tier"""
        intervals = {
            StoreTier.TIER1: 5,    # 5 minutes
            StoreTier.TIER2: 15,   # 15 minutes
            StoreTier.TIER3: 60,   # 60 minutes
            StoreTier.TIER4: 240   # 4 hours
        }
        minutes = intervals.get(tier, 60)
        return datetime.utcnow() + timedelta(minutes=minutes)


class TierManager:
    """
    Manages automatic store tier adjustments based on activity
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def evaluate_and_adjust_tier(self, store_id: UUID):
        """
        Evaluate store activity and adjust tier if needed
        Called after sync operations and order placements
        """
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            return
        
        # Get activity metrics
        metrics = await self._get_activity_metrics(store_id)
        
        # Determine appropriate tier
        new_tier = self._calculate_tier(metrics)
        
        # Update if changed
        if new_tier != store.sync_tier:
            old_tier = store.sync_tier
            store.sync_tier = new_tier
            store.sync_interval_minutes = self._get_sync_interval(new_tier)
            self.db.commit()
            logger.info(f"Store {store_id} tier changed: {old_tier} → {new_tier}")
    
    async def _get_activity_metrics(self, store_id: UUID) -> Dict[str, Any]:
        """Get store activity metrics for tier calculation"""
        from sqlalchemy import func
        from app.models.models import Order
        
        # Orders in last 24 hours
        day_ago = datetime.utcnow() - timedelta(days=1)
        orders_count = self.db.query(func.count(Order.id)).filter(
            and_(Order.store_id == store_id, Order.created_at >= day_ago)
        ).scalar() or 0
        
        # Product updates in last 24 hours
        products_updated = self.db.query(func.count(Product.id)).filter(
            and_(
                Product.store_id == store_id,
                Product.updated_at >= day_ago
            )
        ).scalar() or 0
        
        # Total products
        total_products = self.db.query(func.count(Product.id)).filter(
            Product.store_id == store_id
        ).scalar() or 0
        
        return {
            "orders_per_day": orders_count,
            "products_updated_per_day": products_updated,
            "total_products": total_products
        }
    
    def _calculate_tier(self, metrics: Dict[str, Any]) -> StoreTier:
        """Calculate appropriate tier based on metrics"""
        orders = metrics["orders_per_day"]
        updates = metrics["products_updated_per_day"]
        
        # Tier 1: High activity
        if orders >= 50 or updates >= 100:
            return StoreTier.TIER1
        
        # Tier 2: Medium activity
        elif orders >= 20 or updates >= 30:
            return StoreTier.TIER2
        
        # Tier 3: Low activity
        elif orders >= 5 or updates >= 10:
            return StoreTier.TIER3
        
        # Tier 4: Minimal activity
        else:
            return StoreTier.TIER4
    
    def _get_sync_interval(self, tier: StoreTier) -> int:
        """Get sync interval in minutes for tier"""
        intervals = {
            StoreTier.TIER1: 5,
            StoreTier.TIER2: 15,
            StoreTier.TIER3: 60,
            StoreTier.TIER4: 240
        }
        return intervals.get(tier, 60)
