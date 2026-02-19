# Invoice Ninja Integration

## Overview
Invoice Ninja is integrated into the e-commerce platform for professional invoicing, billing, and payment tracking.

## Access
- **URL**: http://localhost:8080
- **Default Admin**: Created during first run

## Setup Instructions

### 1. Start Services
```bash
docker-compose up -d invoice-ninja-db invoice-ninja invoice-ninja-web
```

### 2. First Time Setup
1. Access http://localhost:8080
2. Complete the setup wizard
3. Configure company details:
   - Company Name
   - Address
   - GST Number (GSTIN)
   - Logo

### 3. Generate API Token
1. Go to Settings → Account Management
2. Click "API Tokens"
3. Create new token with all permissions
4. Copy the token

### 4. Configure E-commerce Integration
Add to your `.env` file:
```
INVOICE_NINJA_URL=http://invoice-ninja:80
INVOICE_NINJA_API_TOKEN=your_api_token_here
```

### 5. Restart Backend
```bash
docker-compose restart backend
```

## API Endpoints

### Clients (Customers)
- `POST /api/v1/invoice-ninja/clients` - Create client
- `GET /api/v1/invoice-ninja/clients/{email}` - Get client by email

### Products
- `POST /api/v1/invoice-ninja/products/sync` - Sync single product
- `POST /api/v1/invoice-ninja/products/bulk-sync` - Bulk sync products

### Invoices
- `POST /api/v1/invoice-ninja/invoices` - Create invoice
- `GET /api/v1/invoice-ninja/invoices/{id}` - Get invoice details
- `POST /api/v1/invoice-ninja/invoices/{id}/send` - Send invoice via email
- `GET /api/v1/invoice-ninja/invoices/{id}/pdf` - Download PDF

### Payments
- `POST /api/v1/invoice-ninja/payments` - Record payment

### Order Sync
- `POST /api/v1/invoice-ninja/orders/{order_id}/sync` - Sync order to Invoice Ninja

### Reports
- `GET /api/v1/invoice-ninja/dashboard` - Dashboard statistics

## India-Specific Configuration

### GST Setup in Invoice Ninja
1. Go to Settings → Tax Settings
2. Add GST rates:
   - GST 0% (Exempt)
   - GST 5% 
   - GST 12%
   - GST 18%
   - GST 28%

### Invoice Format
1. Go to Settings → Invoice Design
2. Select or customize template
3. Add fields:
   - GSTIN (Company and Customer)
   - HSN/SAC Code
   - Place of Supply
   - State Code

### Custom Fields
- Custom Field 1: HSN Code
- Custom Field 2: E-commerce Order ID

## Features

### Auto-Sync
When orders are completed, they can be automatically synced to Invoice Ninja:
- Creates/updates customer
- Creates invoice with line items
- Records payment if already paid
- Sends invoice email (optional)

### PDF Generation
Professional GST-compliant invoices generated automatically.

### Multi-Currency
Supports INR with proper formatting.

### Recurring Invoices
For subscription-based services.

### Quotes/Estimates
Convert to invoice when accepted.

## Customization

### Custom Invoice Template
Place custom templates in `invoice-ninja/config/templates/`

### Company Settings
Configure via web interface or API:
```python
from app.services.invoice_ninja import InvoiceNinjaClient

client = InvoiceNinjaClient()
# Update company settings via API
```

## Troubleshooting

### Connection Issues
```bash
# Check containers
docker-compose ps

# Check logs
docker-compose logs invoice-ninja

# Test connection
curl http://localhost:8080/api/v1/ping
```

### Database Issues
```bash
# Access MySQL
docker exec -it invoice_ninja_db mysql -u ninja -p

# Reset database
docker-compose down -v
docker-compose up -d
```

### PDF Generation Issues
PDF generation uses snappdf. If issues occur:
1. Check container logs
2. Ensure sufficient memory (512MB+)
3. Try switching to phantom.js in settings

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  E-commerce     │     │  Invoice Ninja   │
│  Backend        │────▶│  API             │
│  (FastAPI)      │     │  (Laravel)       │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         │                       │
    ┌────▼────┐           ┌──────▼──────┐
    │PostgreSQL│           │   MySQL     │
    └─────────┘           └─────────────┘
```

## Support
- Invoice Ninja Docs: https://invoiceninja.github.io/
- API Docs: https://api-docs.invoicing.co/
