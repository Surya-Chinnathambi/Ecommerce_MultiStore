"""
Billing Integration API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User
from app.models.billing_models import BillingProvider, SyncDirection, EntityType
from app.schemas.billing_schemas import (
    BillingIntegrationCreate,
    BillingIntegrationUpdate,
    BillingIntegrationResponse,
    SyncRequest,
    SyncLogResponse,
    SyncStats,
    InvoiceExportRequest,
    InvoiceExportBulkResponse,
    ProductImportRequest,
    ProductImportBulkResponse,
    CSVTemplateCreate,
    CSVTemplateUpdate,
    CSVTemplateResponse,
    CSVExportRequest,
    CSVImportRequest,
    FileExportResponse,
    FileImportResponse,
    ConnectionTestRequest,
    ConnectionTestResponse
)
from app.services.billing_service import get_billing_service
from app.services.csv_service import csv_service

router = APIRouter()


# ==================== Integration Management ====================

@router.post("/integrations", response_model=BillingIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration: BillingIntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new billing integration"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_billing_service(db, str(current_user.store_id))
    return service.create_integration(
        name=integration.name,
        provider=integration.provider,
        config=integration.config,
        is_active=integration.is_active,
        auto_sync=integration.auto_sync,
        sync_direction=integration.sync_direction,
        sync_frequency_minutes=integration.sync_frequency_minutes,
        sync_entities=integration.sync_entities,
        field_mapping=integration.field_mapping
    )


@router.get("/integrations", response_model=List[BillingIntegrationResponse])
async def list_integrations(
    provider: Optional[BillingProvider] = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List billing integrations"""
    service = get_billing_service(db, str(current_user.store_id))
    return service.list_integrations(provider=provider, is_active=is_active)


@router.get("/integrations/{integration_id}", response_model=BillingIntegrationResponse)
async def get_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get integration by ID"""
    service = get_billing_service(db, str(current_user.store_id))
    integration = service.get_integration(integration_id)
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return integration


@router.patch("/integrations/{integration_id}", response_model=BillingIntegrationResponse)
async def update_integration(
    integration_id: str,
    updates: BillingIntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update integration"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_billing_service(db, str(current_user.store_id))
    integration = service.update_integration(integration_id, **updates.dict(exclude_unset=True))
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return integration


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete integration"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_billing_service(db, str(current_user.store_id))
    success = service.delete_integration(integration_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")


# ==================== Connection Testing ====================

@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    request: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connection to billing provider"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_billing_service(db, str(current_user.store_id))
    result = service.test_connection(request.provider, request.config)
    
    return ConnectionTestResponse(**result)


# ==================== Sync Operations ====================

@router.post("/integrations/{integration_id}/sync", response_model=SyncLogResponse)
async def sync_data(
    integration_id: str,
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger data sync"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    service = get_billing_service(db, str(current_user.store_id))
    
    try:
        sync_log = await service.sync_data(
            integration_id=integration_id,
            entity_types=sync_request.entity_types,
            direction=sync_request.direction,
            filters=sync_request.filters,
            limit=sync_request.limit
        )
        return sync_log
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/integrations/{integration_id}/sync-logs", response_model=List[SyncLogResponse])
async def get_sync_logs(
    integration_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync logs for integration"""
    from app.models.billing_models import BillingSyncLog
    
    logs = db.query(BillingSyncLog).filter(
        BillingSyncLog.integration_id == integration_id,
        BillingSyncLog.store_id == current_user.store_id
    ).order_by(BillingSyncLog.created_at.desc()).limit(limit).all()
    
    return logs


@router.get("/integrations/{integration_id}/stats", response_model=SyncStats)
async def get_sync_stats(
    integration_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync statistics"""
    service = get_billing_service(db, str(current_user.store_id))
    return service.get_sync_stats(integration_id, days)


# ==================== Invoice Export ====================

@router.post("/export/invoices", response_model=InvoiceExportBulkResponse)
async def export_invoices(
    request: InvoiceExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export invoices to billing system"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # TODO: Implement invoice export
    return InvoiceExportBulkResponse(
        total=len(request.order_ids),
        succeeded=0,
        failed=0,
        exports=[],
        errors=[]
    )


# ==================== CSV/Excel Operations ====================

@router.post("/export/csv", response_model=FileExportResponse)
async def export_to_csv(
    request: CSVExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export data to CSV file"""
    from app.models.models import Order, Product
    from datetime import datetime
    
    # Fetch data based on entity type
    if request.entity_type == EntityType.INVOICE:
        query = db.query(Order).filter(Order.store_id == current_user.store_id)
        
        if request.date_from:
            query = query.filter(Order.created_at >= request.date_from)
        if request.date_to:
            query = query.filter(Order.created_at <= request.date_to)
        
        records = query.limit(request.limit).all()
        
        # Convert to dict format
        data = []
        for order in records:
            data.append({
                'invoice_number': f"INV-{str(order.id)[:8]}",
                'order_id': str(order.id),
                'customer_name': order.customer_name or '',
                'customer_email': order.customer_email or '',
                'date': order.created_at.strftime('%Y-%m-%d'),
                'subtotal': float(order.subtotal or 0),
                'tax': float(order.tax or 0),
                'shipping': float(order.shipping_cost or 0),
                'total': float(order.total),
                'status': order.status,
                'payment_method': order.payment_method or ''
            })
        
        csv_content = csv_service.export_invoices_to_csv(data)
        file_name = f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    elif request.entity_type == EntityType.PRODUCT:
        query = db.query(Product).filter(Product.store_id == current_user.store_id)
        products = query.limit(request.limit).all()
        
        data = []
        for product in products:
            data.append({
                'sku': product.sku,
                'name': product.name,
                'description': product.description or '',
                'price': float(product.selling_price or 0),
                'cost': float(product.cost_price or 0),
                'quantity': product.quantity,
                'category': '',  # Category ID, not name
                'brand': product.attributes.get('brand', '') if product.attributes else '',
                'status': 'active' if product.is_active else 'inactive'
            })
        
        csv_content = csv_service.export_products_to_csv(data)
        file_name = f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    else:
        raise HTTPException(status_code=400, detail=f"Export not supported for {request.entity_type}")
    
    # TODO: Save to S3 or file storage and return URL
    # For now, return as inline data
    
    return FileExportResponse(
        file_url=f"/downloads/{file_name}",
        file_name=file_name,
        file_size=len(csv_content),
        row_count=len(data),
        format="csv",
        expires_at=datetime.utcnow()
    )


@router.post("/import/csv", response_model=FileImportResponse)
async def import_from_csv(
    file: UploadFile = File(...),
    entity_type: EntityType = EntityType.PRODUCT,
    auto_create: bool = True,
    update_existing: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import data from CSV file"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Read CSV content
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    if entity_type == EntityType.PRODUCT:
        products, errors = csv_service.import_products_from_csv(csv_content)
        
        created_ids = []
        updated_ids = []
        failed = 0
        
        # Create/update products
        from app.models.models import Product
        
        for product_data in products:
            try:
                # Map CSV fields to Product model fields
                mapped_data = {
                    'sku': product_data.get('sku'),
                    'name': product_data.get('name'),
                    'description': product_data.get('description', ''),
                    'selling_price': product_data.get('price', 0.0),
                    'mrp': product_data.get('price', 0.0),  # Use price as MRP by default
                    'cost_price': product_data.get('cost'),
                    'quantity': product_data.get('quantity', 0),
                    'external_id': product_data.get('sku'),  # Use SKU as external_id
                    'slug': product_data.get('name', '').lower().replace(' ', '-'),
                }
                
                # Optional fields
                if product_data.get('category'):
                    mapped_data['short_description'] = f"Category: {product_data['category']}"
                
                if product_data.get('brand'):
                    # Store brand in attributes JSON
                    mapped_data['attributes'] = {'brand': product_data['brand']}
                
                # Check if product exists
                existing = db.query(Product).filter(
                    Product.store_id == current_user.store_id,
                    Product.sku == product_data['sku']
                ).first()
                
                if existing and update_existing:
                    # Update existing
                    for key, value in mapped_data.items():
                        if value is not None and hasattr(existing, key):
                            setattr(existing, key, value)
                    updated_ids.append(str(existing.id))
                
                elif not existing and auto_create:
                    # Create new
                    new_product = Product(
                        store_id=current_user.store_id,
                        **mapped_data
                    )
                    db.add(new_product)
                    db.flush()
                    created_ids.append(str(new_product.id))
            
            except Exception as e:
                failed += 1
                errors.append({'sku': product_data.get('sku'), 'error': str(e)})
        
        db.commit()
        
        return FileImportResponse(
            total_rows=len(products) + len(errors),
            processed=len(products),
            succeeded=len(created_ids) + len(updated_ids),
            failed=failed,
            skipped=len(errors),
            errors=errors[:100],  # Limit errors returned
            created_ids=created_ids,
            updated_ids=updated_ids
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Import not supported for {entity_type}")


@router.get("/sample-csv/{entity_type}")
async def download_sample_csv(
    entity_type: str,
    current_user: User = Depends(get_current_user)
):
    """Download sample CSV template"""
    from fastapi.responses import Response
    
    csv_content = csv_service.generate_sample_csv(entity_type)
    
    if not csv_content:
        raise HTTPException(status_code=404, detail="Sample not available for this entity type")
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=sample_{entity_type}.csv"
        }
    )


# ==================== CSV Templates ====================

@router.post("/csv-templates", response_model=CSVTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_csv_template(
    template: CSVTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create CSV template"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from app.models.billing_models import CSVTemplate
    
    csv_template = CSVTemplate(
        store_id=current_user.store_id,
        **template.dict()
    )
    
    db.add(csv_template)
    db.commit()
    db.refresh(csv_template)
    
    return csv_template


@router.get("/csv-templates", response_model=List[CSVTemplateResponse])
async def list_csv_templates(
    entity_type: Optional[EntityType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List CSV templates"""
    from app.models.billing_models import CSVTemplate
    
    query = db.query(CSVTemplate).filter(
        CSVTemplate.store_id == current_user.store_id
    )
    
    if entity_type:
        query = query.filter(CSVTemplate.entity_type == entity_type)
    
    return query.all()


@router.get("/csv-templates/{template_id}", response_model=CSVTemplateResponse)
async def get_csv_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get CSV template"""
    from app.models.billing_models import CSVTemplate
    
    template = db.query(CSVTemplate).filter(
        CSVTemplate.id == template_id,
        CSVTemplate.store_id == current_user.store_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


# ==================== Supported Providers ====================

@router.get("/providers")
async def list_providers():
    """List supported billing providers"""
    return {
        "providers": [
            {
                "id": "quickbooks",
                "name": "QuickBooks Online",
                "description": "Intuit QuickBooks Online accounting software",
                "features": ["invoices", "products", "customers", "payments"],
                "requires_oauth": True
            },
            {
                "id": "xero",
                "name": "Xero",
                "description": "Xero cloud accounting software",
                "features": ["invoices", "products", "customers", "payments"],
                "requires_oauth": True
            },
            {
                "id": "zoho_books",
                "name": "Zoho Books",
                "description": "Zoho online accounting software",
                "features": ["invoices", "products", "customers"],
                "requires_oauth": True
            },
            {
                "id": "tally",
                "name": "Tally ERP",
                "description": "Tally desktop accounting software (India)",
                "features": ["invoices", "products", "customers"],
                "requires_oauth": False
            },
            {
                "id": "sage",
                "name": "Sage Business Cloud",
                "description": "Sage accounting and business management",
                "features": ["invoices", "products", "customers"],
                "requires_oauth": True
            },
            {
                "id": "custom_api",
                "name": "Custom API",
                "description": "Connect to your custom billing API",
                "features": ["configurable"],
                "requires_oauth": False
            },
            {
                "id": "csv_excel",
                "name": "CSV/Excel",
                "description": "Import/Export via CSV or Excel files",
                "features": ["invoices", "products", "customers"],
                "requires_oauth": False
            }
        ]
    }
