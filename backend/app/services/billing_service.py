"""
Billing Integration Service
Main orchestrator for billing software integrations
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.billing_models import (
    BillingIntegration,
    BillingSyncLog,
    InvoiceExport,
    ProductImport,
    CSVTemplate,
    BillingProvider,
    SyncDirection,
    SyncStatus,
    EntityType
)
from app.models.models import Order, Product
from app.services.csv_service import csv_service

logger = logging.getLogger(__name__)


class BillingIntegrationService:
    """Service for managing billing integrations"""
    
    def __init__(self, db: Session, store_id: str):
        self.db = db
        self.store_id = store_id
    
    # ==================== Integration Management ====================
    
    def create_integration(
        self,
        name: str,
        provider: BillingProvider,
        config: Dict[str, Any],
        **kwargs
    ) -> BillingIntegration:
        """Create new billing integration"""
        integration = BillingIntegration(
            store_id=self.store_id,
            name=name,
            provider=provider,
            config=config,
            **kwargs
        )
        
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        
        logger.info(f"Created billing integration: {name} ({provider})")
        return integration
    
    def get_integration(self, integration_id: str) -> Optional[BillingIntegration]:
        """Get integration by ID"""
        return self.db.query(BillingIntegration).filter(
            BillingIntegration.id == integration_id,
            BillingIntegration.store_id == self.store_id
        ).first()
    
    def list_integrations(
        self,
        provider: Optional[BillingProvider] = None,
        is_active: bool = True
    ) -> List[BillingIntegration]:
        """List integrations"""
        query = self.db.query(BillingIntegration).filter(
            BillingIntegration.store_id == self.store_id
        )
        
        if provider:
            query = query.filter(BillingIntegration.provider == provider)
        
        if is_active is not None:
            query = query.filter(BillingIntegration.is_active == is_active)
        
        return query.all()
    
    def update_integration(
        self,
        integration_id: str,
        **kwargs
    ) -> Optional[BillingIntegration]:
        """Update integration"""
        integration = self.get_integration(integration_id)
        if not integration:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(integration, key):
                setattr(integration, key, value)
        
        self.db.commit()
        self.db.refresh(integration)
        
        return integration
    
    def delete_integration(self, integration_id: str) -> bool:
        """Delete integration"""
        integration = self.get_integration(integration_id)
        if not integration:
            return False
        
        self.db.delete(integration)
        self.db.commit()
        
        logger.info(f"Deleted billing integration: {integration_id}")
        return True
    
    def test_connection(
        self,
        provider: BillingProvider,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test connection to billing provider"""
        try:
            # TODO: Implement actual connection testing for each provider
            if provider == BillingProvider.QUICKBOOKS:
                return self._test_quickbooks_connection(config)
            elif provider == BillingProvider.XERO:
                return self._test_xero_connection(config)
            elif provider == BillingProvider.TALLY:
                return self._test_tally_connection(config)
            elif provider == BillingProvider.CUSTOM_API:
                return self._test_custom_api_connection(config)
            elif provider == BillingProvider.CSV_EXCEL:
                return {'success': True, 'message': "CSV/Excel doesn't require connection test"}
            else:
                return {'success': False, 'message': f'Provider {provider} not implemented yet'}
        
        except Exception as e:
            logger.error(f"Connection test failed for {provider}: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==================== Sync Operations ====================
    
    async def sync_data(
        self,
        integration_id: str,
        entity_types: List[EntityType],
        direction: SyncDirection,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> BillingSyncLog:
        """Sync data with billing system"""
        integration = self.get_integration(integration_id)
        if not integration:
            raise ValueError(f"Integration not found: {integration_id}")
        
        # Create sync log
        sync_log = BillingSyncLog(
            integration_id=integration_id,
            store_id=self.store_id,
            sync_type="manual",
            entity_type=entity_types[0],  # Primary entity type
            direction=direction,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            total_processed = 0
            total_succeeded = 0
            total_failed = 0
            
            for entity_type in entity_types:
                if direction == SyncDirection.PUSH or direction == SyncDirection.BIDIRECTIONAL:
                    # Export to billing system
                    result = await self._export_data(
                        integration, entity_type, filters, limit
                    )
                    total_processed += result['processed']
                    total_succeeded += result['succeeded']
                    total_failed += result['failed']
                
                if direction == SyncDirection.PULL or direction == SyncDirection.BIDIRECTIONAL:
                    # Import from billing system
                    result = await self._import_data(
                        integration, entity_type, filters, limit
                    )
                    total_processed += result['processed']
                    total_succeeded += result['succeeded']
                    total_failed += result['failed']
            
            # Update sync log
            sync_log.status = SyncStatus.COMPLETED if total_failed == 0 else SyncStatus.PARTIAL
            sync_log.records_processed = total_processed
            sync_log.records_succeeded = total_succeeded
            sync_log.records_failed = total_failed
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            sync_log.summary = f"Synced {total_succeeded}/{total_processed} records"
            
            # Update integration
            integration.last_sync_at = datetime.utcnow()
            integration.last_sync_status = sync_log.status.value
            integration.total_syncs += 1
            if total_failed == 0:
                integration.successful_syncs += 1
            else:
                integration.failed_syncs += 1
            
            self.db.commit()
            self.db.refresh(sync_log)
            
            logger.info(f"Sync completed: {integration.name} - {total_succeeded}/{total_processed} records")
            return sync_log
        
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            
            integration.last_sync_at = datetime.utcnow()
            integration.last_sync_status = "failed"
            integration.last_sync_message = str(e)
            integration.failed_syncs += 1
            
            self.db.commit()
            raise
    
    async def _export_data(
        self,
        integration: BillingIntegration,
        entity_type: EntityType,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Export data to billing system"""
        if entity_type == EntityType.INVOICE:
            return await self._export_invoices(integration, filters, limit)
        elif entity_type == EntityType.PRODUCT:
            return await self._export_products(integration, filters, limit)
        elif entity_type == EntityType.CUSTOMER:
            return await self._export_customers(integration, filters, limit)
        else:
            logger.warning(f"Export not implemented for entity type: {entity_type}")
            return {'processed': 0, 'succeeded': 0, 'failed': 0}
    
    async def _import_data(
        self,
        integration: BillingIntegration,
        entity_type: EntityType,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Import data from billing system"""
        if entity_type == EntityType.PRODUCT:
            return await self._import_products(integration, filters, limit)
        elif entity_type == EntityType.CUSTOMER:
            return await self._import_customers(integration, filters, limit)
        else:
            logger.warning(f"Import not implemented for entity type: {entity_type}")
            return {'processed': 0, 'succeeded': 0, 'failed': 0}
    
    # ==================== Invoice Export ====================
    
    async def _export_invoices(
        self,
        integration: BillingIntegration,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Export invoices to billing system"""
        query = self.db.query(Order).filter(Order.store_id == self.store_id)
        
        if filters:
            if filters.get('date_from'):
                query = query.filter(Order.created_at >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(Order.created_at <= filters['date_to'])
            if filters.get('status'):
                query = query.filter(Order.status == filters['status'])
        
        if limit:
            query = query.limit(limit)
        
        orders = query.all()
        
        succeeded = 0
        failed = 0
        
        for order in orders:
            try:
                # Create invoice export record
                invoice_number = f"INV-{order.id[:8]}"
                
                invoice_export = InvoiceExport(
                    order_id=order.id,
                    integration_id=integration.id,
                    store_id=self.store_id,
                    invoice_number=invoice_number,
                    provider=integration.provider,
                    invoice_data=self._format_invoice_data(order),
                    status="pending"
                )
                
                self.db.add(invoice_export)
                
                # For CSV/Excel, mark as exported (actual file generation happens separately)
                if integration.provider == BillingProvider.CSV_EXCEL:
                    invoice_export.status = "exported"
                    invoice_export.exported_at = datetime.utcnow()
                else:
                    # TODO: Actually send to external billing system
                    pass
                
                succeeded += 1
            
            except Exception as e:
                logger.error(f"Failed to export invoice for order {order.id}: {e}")
                failed += 1
        
        self.db.commit()
        
        return {'processed': len(orders), 'succeeded': succeeded, 'failed': failed}
    
    def _format_invoice_data(self, order: Order) -> Dict[str, Any]:
        """Format order as invoice data"""
        return {
            'invoice_number': f"INV-{str(order.id)[:8]}",
            'order_id': str(order.id),
            'customer_id': str(order.customer_id) if order.customer_id else None,
            'date': order.created_at.isoformat(),
            'subtotal': float(order.subtotal or 0),
            'tax': float(order.tax or 0),
            'shipping': float(order.shipping_cost or 0),
            'discount': float(order.discount or 0),
            'total': float(order.total),
            'status': order.status,
            'payment_method': order.payment_method,
            'items': [
                {
                    'sku': item.product_sku,
                    'name': item.product_name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': float(item.quantity * item.price)
                }
                for item in order.order_items
            ]
        }
    
    # ==================== Product Operations ====================
    
    async def _export_products(
        self,
        integration: BillingIntegration,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Export products to billing system"""
        query = self.db.query(Product).filter(Product.store_id == self.store_id)
        
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        
        # TODO: Actually send to external billing system
        
        return {'processed': len(products), 'succeeded': len(products), 'failed': 0}
    
    async def _import_products(
        self,
        integration: BillingIntegration,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Import products from billing system"""
        # TODO: Fetch from external billing system
        
        return {'processed': 0, 'succeeded': 0, 'failed': 0}
    
    async def _export_customers(
        self,
        integration: BillingIntegration,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Export customers to billing system"""
        # TODO: Implement customer export
        return {'processed': 0, 'succeeded': 0, 'failed': 0}
    
    async def _import_customers(
        self,
        integration: BillingIntegration,
        filters: Optional[Dict[str, Any]],
        limit: Optional[int]
    ) -> Dict[str, int]:
        """Import customers from billing system"""
        # TODO: Implement customer import
        return {'processed': 0, 'succeeded': 0, 'failed': 0}
    
    # ==================== Connection Testing ====================
    
    def _test_quickbooks_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test QuickBooks connection"""
        # TODO: Implement QuickBooks OAuth flow and test
        return {'success': True, 'message': 'QuickBooks connection test (placeholder)'}
    
    def _test_xero_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Xero connection"""
        # TODO: Implement Xero OAuth flow and test
        return {'success': True, 'message': 'Xero connection test (placeholder)'}
    
    def _test_tally_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Tally connection"""
        # TODO: Implement Tally XML-RPC connection test
        return {'success': True, 'message': 'Tally connection test (placeholder)'}
    
    def _test_custom_api_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test custom API connection"""
        # TODO: Make test API call
        return {'success': True, 'message': 'Custom API connection test (placeholder)'}
    
    # ==================== Statistics ====================
    
    def get_sync_stats(self, integration_id: str, days: int = 30) -> Dict[str, Any]:
        """Get sync statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(BillingSyncLog).filter(
            BillingSyncLog.integration_id == integration_id,
            BillingSyncLog.created_at >= since
        ).all()
        
        total = len(logs)
        succeeded = len([l for l in logs if l.status == SyncStatus.COMPLETED])
        failed = len([l for l in logs if l.status == SyncStatus.FAILED])
        
        avg_duration = sum([l.duration_seconds for l in logs if l.duration_seconds]) / total if total > 0 else 0
        
        by_entity = {}
        for log in logs:
            entity = log.entity_type.value
            by_entity[entity] = by_entity.get(entity, 0) + 1
        
        return {
            'total_syncs': total,
            'successful_syncs': succeeded,
            'failed_syncs': failed,
            'success_rate': (succeeded / total * 100) if total > 0 else 0,
            'avg_duration_seconds': avg_duration,
            'by_entity_type': by_entity,
            'recent_logs': logs[:10]
        }


def get_billing_service(db: Session, store_id: str) -> BillingIntegrationService:
    """Get billing integration service instance"""
    return BillingIntegrationService(db, store_id)
