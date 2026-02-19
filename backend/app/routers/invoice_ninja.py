"""
Invoice Ninja Integration API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.auth_models import User
from app.models.models import Order
from app.services.invoice_ninja import InvoiceNinjaClient, InvoiceNinjaSync

router = APIRouter()


# ============================================
# SCHEMAS
# ============================================

class ClientCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    gstin: Optional[str] = None


class ProductSync(BaseModel):
    sku: str
    name: str
    price: Decimal
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[Decimal] = Decimal("18")


class InvoiceItemCreate(BaseModel):
    sku: str
    name: str
    price: Decimal
    quantity: int = 1
    gst_rate: Optional[Decimal] = Decimal("18")
    hsn_code: Optional[str] = None


class InvoiceCreate(BaseModel):
    client_email: str
    items: List[InvoiceItemCreate]
    order_id: Optional[str] = None
    notes: Optional[str] = None
    discount: Optional[Decimal] = None
    send_email: bool = False


class PaymentRecord(BaseModel):
    invoice_id: str
    amount: Decimal
    payment_method: str = "cash"
    transaction_ref: Optional[str] = None


# ============================================
# CLIENT ENDPOINTS
# ============================================

@router.post("/clients", response_model=dict)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new client in Invoice Ninja"""
    try:
        client = InvoiceNinjaClient()
        
        address = None
        if client_data.address_line1:
            address = {
                "line1": client_data.address_line1,
                "city": client_data.city,
                "state": client_data.state,
                "postal_code": client_data.postal_code
            }
        
        result = await client.create_client(
            name=client_data.name,
            email=client_data.email,
            phone=client_data.phone,
            address=address,
            gstin=client_data.gstin
        )
        
        return {
            "success": True,
            "message": "Client created successfully",
            "data": {
                "client_id": result["data"]["id"],
                "name": client_data.name
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )


@router.get("/clients/{email}", response_model=dict)
async def get_client_by_email(
    email: str,
    current_user: User = Depends(get_current_active_user)
):
    """Find client by email"""
    try:
        client = InvoiceNinjaClient()
        result = await client.find_client_by_email(email)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# PRODUCT ENDPOINTS
# ============================================

@router.post("/products/sync", response_model=dict)
async def sync_product(
    product_data: ProductSync,
    current_user: User = Depends(get_current_active_user)
):
    """Sync a product to Invoice Ninja"""
    try:
        client = InvoiceNinjaClient()
        
        result = await client.sync_product(
            sku=product_data.sku,
            name=product_data.name,
            price=product_data.price,
            description=product_data.description,
            hsn_code=product_data.hsn_code,
            gst_rate=product_data.gst_rate
        )
        
        return {
            "success": True,
            "message": "Product synced successfully",
            "data": {
                "product_id": result["data"]["id"],
                "sku": product_data.sku
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync product: {str(e)}"
        )


@router.post("/products/bulk-sync", response_model=dict)
async def bulk_sync_products(
    products: List[ProductSync],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Bulk sync products to Invoice Ninja"""
    try:
        sync_service = InvoiceNinjaSync()
        
        products_data = [
            {
                "sku": p.sku,
                "name": p.name,
                "price": float(p.price),
                "description": p.description,
                "hsn_code": p.hsn_code,
                "gst_rate": float(p.gst_rate) if p.gst_rate else 0
            }
            for p in products
        ]
        
        result = await sync_service.sync_products(products_data)
        
        return {
            "success": True,
            "message": f"Synced {result['synced']} products",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# INVOICE ENDPOINTS
# ============================================

@router.post("/invoices", response_model=dict)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new invoice"""
    try:
        client = InvoiceNinjaClient()
        
        # Find or create client
        existing_client = await client.find_client_by_email(invoice_data.client_email)
        
        if not existing_client:
            # Create a basic client
            client_result = await client.create_client(
                name=invoice_data.client_email.split("@")[0],
                email=invoice_data.client_email
            )
            client_id = client_result["data"]["id"]
        else:
            client_id = existing_client["id"]
        
        # Prepare items
        items = [
            {
                "sku": item.sku,
                "name": item.name,
                "price": float(item.price),
                "quantity": item.quantity,
                "gst_rate": float(item.gst_rate) if item.gst_rate else 0,
                "hsn_code": item.hsn_code
            }
            for item in invoice_data.items
        ]
        
        # Create invoice
        result = await client.create_invoice(
            client_id=client_id,
            items=items,
            order_id=invoice_data.order_id,
            notes=invoice_data.notes,
            discount=invoice_data.discount
        )
        
        invoice_id = result["data"]["id"]
        
        # Send email if requested
        if invoice_data.send_email:
            await client.send_invoice(invoice_id)
        
        return {
            "success": True,
            "message": "Invoice created successfully",
            "data": {
                "invoice_id": invoice_id,
                "invoice_number": result["data"].get("number"),
                "total": result["data"].get("amount"),
                "email_sent": invoice_data.send_email
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )


@router.get("/invoices/{invoice_id}", response_model=dict)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get invoice details"""
    try:
        client = InvoiceNinjaClient()
        result = await client.get_invoice(invoice_id)
        
        return {
            "success": True,
            "data": result["data"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/invoices/{invoice_id}/send", response_model=dict)
async def send_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Send invoice via email"""
    try:
        client = InvoiceNinjaClient()
        await client.send_invoice(invoice_id)
        
        return {
            "success": True,
            "message": "Invoice sent successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download invoice as PDF"""
    from fastapi.responses import Response
    
    try:
        client = InvoiceNinjaClient()
        pdf_content = await client.download_invoice_pdf(invoice_id)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# PAYMENT ENDPOINTS
# ============================================

@router.post("/payments", response_model=dict)
async def record_payment(
    payment_data: PaymentRecord,
    current_user: User = Depends(get_current_active_user)
):
    """Record a payment for an invoice"""
    try:
        client = InvoiceNinjaClient()
        
        result = await client.mark_invoice_paid(
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            transaction_ref=payment_data.transaction_ref
        )
        
        return {
            "success": True,
            "message": "Payment recorded successfully",
            "data": {
                "payment_id": result["data"]["id"],
                "amount": float(payment_data.amount)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# ORDER SYNC ENDPOINTS
# ============================================

@router.post("/orders/{order_id}/sync", response_model=dict)
async def sync_order_to_invoice(
    order_id: str,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync an e-commerce order to Invoice Ninja as an invoice"""
    try:
        # Get order from database
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        sync_service = InvoiceNinjaSync()
        
        # Prepare order data
        order_data = {
            "order_id": str(order.id),
            "customer_name": order.user.full_name if order.user else "Customer",
            "customer_email": order.user.email if order.user else "",
            "customer_phone": order.user.phone if order.user else "",
            "shipping_address": {
                "line1": order.shipping_address.address_line1 if order.shipping_address else "",
                "city": order.shipping_address.city if order.shipping_address else "",
                "state": order.shipping_address.state if order.shipping_address else "",
                "postal_code": order.shipping_address.postal_code if order.shipping_address else ""
            },
            "items": [
                {
                    "sku": item.product.sku if item.product else "",
                    "name": item.product.name if item.product else "",
                    "price": float(item.unit_price),
                    "quantity": item.quantity,
                    "gst_rate": 18  # Default GST
                }
                for item in order.items
            ],
            "discount": float(order.discount_amount) if order.discount_amount else 0,
            "total": float(order.total_amount),
            "payment_status": order.payment_status,
            "payment_method": order.payment_method or "cash",
            "transaction_id": order.transaction_id
        }
        
        result = await sync_service.sync_order_as_invoice(order_data)
        
        # Send email if requested
        if send_email:
            client = InvoiceNinjaClient()
            await client.send_invoice(result["data"]["id"])
        
        return {
            "success": True,
            "message": "Order synced to Invoice Ninja",
            "data": {
                "order_id": order_id,
                "invoice_id": result["data"]["id"],
                "invoice_number": result["data"].get("number")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# REPORTS ENDPOINTS
# ============================================

@router.get("/dashboard", response_model=dict)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get Invoice Ninja dashboard statistics"""
    try:
        client = InvoiceNinjaClient()
        result = await client.get_dashboard_stats()
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# HEALTH CHECK
# ============================================

@router.get("/health", response_model=dict)
async def check_invoice_ninja_health():
    """Check Invoice Ninja connection"""
    import os
    
    ninja_url = os.getenv("INVOICE_NINJA_URL", "http://invoice-ninja:80")
    has_token = bool(os.getenv("INVOICE_NINJA_API_TOKEN"))
    
    return {
        "success": True,
        "data": {
            "invoice_ninja_url": ninja_url,
            "api_token_configured": has_token,
            "status": "configured" if has_token else "not_configured"
        }
    }
