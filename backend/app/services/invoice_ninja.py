"""
Invoice Ninja Integration Service
Sync orders, customers, and products with Invoice Ninja billing system
"""
import httpx
from typing import Optional, Dict, List, Any
from decimal import Decimal
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class InvoiceNinjaClient:
    """
    Invoice Ninja API v5 Client
    Documentation: https://api-docs.invoicing.co/
    """
    
    def __init__(
        self,
        base_url: str = None,
        api_token: str = None
    ):
        self.base_url = (base_url or os.getenv("INVOICE_NINJA_URL", "http://invoice-ninja:80")).rstrip("/")
        self.api_token = api_token or os.getenv("INVOICE_NINJA_API_TOKEN", "")
        self.headers = {
            "X-Api-Token": self.api_token,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Dict:
        """Make API request to Invoice Ninja"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Invoice Ninja API error: {e}")
            raise
    
    # ============================================
    # CLIENT (CUSTOMER) METHODS
    # ============================================
    
    async def create_client(
        self,
        name: str,
        email: str,
        phone: str = None,
        address: Dict = None,
        gstin: str = None,
        custom_values: Dict = None
    ) -> Dict:
        """Create a new client in Invoice Ninja"""
        data = {
            "name": name,
            "contacts": [
                {
                    "first_name": name.split()[0] if name else "",
                    "last_name": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else "",
                    "email": email,
                    "phone": phone or ""
                }
            ],
            "settings": {
                "currency_id": "4",  # INR
                "language_id": "1"   # English
            }
        }
        
        if address:
            data.update({
                "address1": address.get("line1", ""),
                "address2": address.get("line2", ""),
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "postal_code": address.get("postal_code", ""),
                "country_id": "356"  # India
            })
        
        if gstin:
            data["vat_number"] = gstin
        
        if custom_values:
            data["custom_value1"] = custom_values.get("custom1", "")
            data["custom_value2"] = custom_values.get("custom2", "")
        
        return await self._request("POST", "clients", data)
    
    async def get_client(self, client_id: str) -> Dict:
        """Get client by ID"""
        return await self._request("GET", f"clients/{client_id}")
    
    async def find_client_by_email(self, email: str) -> Optional[Dict]:
        """Find client by email"""
        result = await self._request("GET", "clients", params={"email": email})
        clients = result.get("data", [])
        return clients[0] if clients else None
    
    async def update_client(self, client_id: str, data: Dict) -> Dict:
        """Update client"""
        return await self._request("PUT", f"clients/{client_id}", data)
    
    # ============================================
    # PRODUCT METHODS
    # ============================================
    
    async def create_product(
        self,
        name: str,
        price: Decimal,
        description: str = None,
        sku: str = None,
        hsn_code: str = None,
        gst_rate: Decimal = None
    ) -> Dict:
        """Create a new product in Invoice Ninja"""
        data = {
            "product_key": sku or name[:50],
            "notes": description or "",
            "cost": 0,
            "price": float(price),
            "quantity": 1,
            "tax_name1": "GST" if gst_rate else "",
            "tax_rate1": float(gst_rate) if gst_rate else 0,
            "custom_value1": hsn_code or ""  # Store HSN in custom field
        }
        
        return await self._request("POST", "products", data)
    
    async def get_product(self, product_id: str) -> Dict:
        """Get product by ID"""
        return await self._request("GET", f"products/{product_id}")
    
    async def find_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Find product by SKU"""
        result = await self._request("GET", "products", params={"product_key": sku})
        products = result.get("data", [])
        return products[0] if products else None
    
    async def sync_product(
        self,
        sku: str,
        name: str,
        price: Decimal,
        description: str = None,
        hsn_code: str = None,
        gst_rate: Decimal = None
    ) -> Dict:
        """Sync product - create or update"""
        existing = await self.find_product_by_sku(sku)
        
        data = {
            "product_key": sku,
            "notes": description or name,
            "price": float(price),
            "tax_name1": "GST" if gst_rate else "",
            "tax_rate1": float(gst_rate) if gst_rate else 0,
            "custom_value1": hsn_code or ""
        }
        
        if existing:
            return await self._request("PUT", f"products/{existing['id']}", data)
        else:
            return await self._request("POST", "products", data)
    
    # ============================================
    # INVOICE METHODS
    # ============================================
    
    async def create_invoice(
        self,
        client_id: str,
        items: List[Dict],
        order_id: str = None,
        notes: str = None,
        due_date: str = None,
        discount: Decimal = None,
        po_number: str = None
    ) -> Dict:
        """Create a new invoice"""
        line_items = []
        
        for item in items:
            line_items.append({
                "product_key": item.get("sku", ""),
                "notes": item.get("name", ""),
                "cost": float(item.get("price", 0)),
                "quantity": float(item.get("quantity", 1)),
                "tax_name1": "GST" if item.get("gst_rate") else "",
                "tax_rate1": float(item.get("gst_rate", 0)),
                "custom_value1": item.get("hsn_code", "")
            })
        
        data = {
            "client_id": client_id,
            "line_items": line_items,
            "auto_bill_enabled": False,
            "uses_inclusive_taxes": True,  # GST inclusive
            "custom_value1": order_id or "",  # Store order reference
            "public_notes": notes or "",
            "po_number": po_number or order_id or ""
        }
        
        if due_date:
            data["due_date"] = due_date
        
        if discount:
            data["discount"] = float(discount)
            data["is_amount_discount"] = True
        
        return await self._request("POST", "invoices", data)
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        """Get invoice by ID"""
        return await self._request("GET", f"invoices/{invoice_id}")
    
    async def find_invoice_by_order(self, order_id: str) -> Optional[Dict]:
        """Find invoice by order ID (stored in custom field)"""
        result = await self._request("GET", "invoices", params={"custom_value1": order_id})
        invoices = result.get("data", [])
        return invoices[0] if invoices else None
    
    async def send_invoice(self, invoice_id: str) -> Dict:
        """Mark invoice as sent and email to client"""
        return await self._request("POST", f"invoices/{invoice_id}/email")
    
    async def mark_invoice_paid(
        self,
        invoice_id: str,
        amount: Decimal,
        payment_method: str = "cash",
        transaction_ref: str = None
    ) -> Dict:
        """Record payment for invoice"""
        
        # Payment type mapping
        payment_types = {
            "cash": "1",
            "card": "2",
            "upi": "15",
            "bank_transfer": "5",
            "razorpay": "15",
            "stripe": "2"
        }
        
        data = {
            "invoices": [
                {
                    "invoice_id": invoice_id,
                    "amount": float(amount)
                }
            ],
            "type_id": payment_types.get(payment_method, "1"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_reference": transaction_ref or ""
        }
        
        return await self._request("POST", "payments", data)
    
    async def download_invoice_pdf(self, invoice_id: str) -> bytes:
        """Download invoice as PDF"""
        url = f"{self.base_url}/api/v1/invoices/{invoice_id}/download"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.content
    
    # ============================================
    # QUOTE METHODS
    # ============================================
    
    async def create_quote(
        self,
        client_id: str,
        items: List[Dict],
        valid_until: str = None,
        notes: str = None
    ) -> Dict:
        """Create a quote/estimate"""
        line_items = [
            {
                "product_key": item.get("sku", ""),
                "notes": item.get("name", ""),
                "cost": float(item.get("price", 0)),
                "quantity": float(item.get("quantity", 1)),
                "tax_name1": "GST" if item.get("gst_rate") else "",
                "tax_rate1": float(item.get("gst_rate", 0))
            }
            for item in items
        ]
        
        data = {
            "client_id": client_id,
            "line_items": line_items,
            "public_notes": notes or "",
            "valid_until": valid_until
        }
        
        return await self._request("POST", "quotes", data)
    
    async def convert_quote_to_invoice(self, quote_id: str) -> Dict:
        """Convert quote to invoice"""
        return await self._request("POST", f"quotes/{quote_id}/convert")
    
    # ============================================
    # RECURRING INVOICE METHODS
    # ============================================
    
    async def create_recurring_invoice(
        self,
        client_id: str,
        items: List[Dict],
        frequency: str = "monthly",  # daily, weekly, monthly, yearly
        start_date: str = None,
        auto_bill: bool = False
    ) -> Dict:
        """Create a recurring invoice"""
        frequency_map = {
            "daily": "1",
            "weekly": "2",
            "biweekly": "3",
            "monthly": "4",
            "quarterly": "5",
            "yearly": "6"
        }
        
        line_items = [
            {
                "product_key": item.get("sku", ""),
                "notes": item.get("name", ""),
                "cost": float(item.get("price", 0)),
                "quantity": float(item.get("quantity", 1))
            }
            for item in items
        ]
        
        data = {
            "client_id": client_id,
            "line_items": line_items,
            "frequency_id": frequency_map.get(frequency, "4"),
            "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
            "auto_bill_enabled": auto_bill
        }
        
        return await self._request("POST", "recurring_invoices", data)
    
    # ============================================
    # REPORT METHODS
    # ============================================
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        return await self._request("GET", "dashboard")
    
    async def get_invoice_report(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """Get invoice report"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self._request("GET", "reports/invoices", params=params)


class InvoiceNinjaSync:
    """
    Sync service between E-commerce and Invoice Ninja
    """
    
    def __init__(self, client: InvoiceNinjaClient = None):
        self.client = client or InvoiceNinjaClient()
    
    async def sync_customer(self, customer: Dict) -> str:
        """Sync customer to Invoice Ninja, return client_id"""
        email = customer.get("email", "")
        
        # Check if exists
        existing = await self.client.find_client_by_email(email)
        
        if existing:
            # Update
            await self.client.update_client(existing["id"], {
                "name": customer.get("name", ""),
                "address1": customer.get("address", {}).get("line1", ""),
                "city": customer.get("address", {}).get("city", "")
            })
            return existing["id"]
        else:
            # Create
            result = await self.client.create_client(
                name=customer.get("name", "Customer"),
                email=email,
                phone=customer.get("phone"),
                address=customer.get("address"),
                gstin=customer.get("gstin")
            )
            return result["data"]["id"]
    
    async def sync_order_as_invoice(self, order: Dict) -> Dict:
        """
        Sync e-commerce order as Invoice Ninja invoice
        """
        # First sync customer
        client_id = await self.sync_customer({
            "name": order.get("customer_name", ""),
            "email": order.get("customer_email", ""),
            "phone": order.get("customer_phone", ""),
            "address": order.get("shipping_address", {}),
            "gstin": order.get("gstin")
        })
        
        # Prepare items
        items = []
        for item in order.get("items", []):
            items.append({
                "sku": item.get("sku", ""),
                "name": item.get("name", ""),
                "price": item.get("price", 0),
                "quantity": item.get("quantity", 1),
                "gst_rate": item.get("gst_rate", 18),
                "hsn_code": item.get("hsn_code", "")
            })
        
        # Create invoice
        invoice = await self.client.create_invoice(
            client_id=client_id,
            items=items,
            order_id=order.get("order_id", ""),
            notes=order.get("notes", ""),
            discount=Decimal(str(order.get("discount", 0)))
        )
        
        # If order is paid, record payment
        if order.get("payment_status") == "paid":
            await self.client.mark_invoice_paid(
                invoice_id=invoice["data"]["id"],
                amount=Decimal(str(order.get("total", 0))),
                payment_method=order.get("payment_method", "cash"),
                transaction_ref=order.get("transaction_id")
            )
        
        return invoice
    
    async def sync_products(self, products: List[Dict]) -> Dict:
        """Bulk sync products to Invoice Ninja"""
        synced = 0
        errors = []
        
        for product in products:
            try:
                await self.client.sync_product(
                    sku=product.get("sku", ""),
                    name=product.get("name", ""),
                    price=Decimal(str(product.get("price", 0))),
                    description=product.get("description", ""),
                    hsn_code=product.get("hsn_code", ""),
                    gst_rate=Decimal(str(product.get("gst_rate", 0)))
                )
                synced += 1
            except Exception as e:
                errors.append({"sku": product.get("sku"), "error": str(e)})
        
        return {
            "synced": synced,
            "errors": errors
        }
