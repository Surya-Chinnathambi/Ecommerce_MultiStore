# KasaPOS Integration Guide
## For Tamil Nadu Grocery Shops

This guide will help you integrate your KasaPOS billing software with the e-commerce platform.

---

## 📋 Prerequisites

1. **KasaPOS** billing software installed and running
2. **Python 3.8+** installed on your computer
3. **Store ID and API Key** from platform administrator
4. **Network access** to the e-commerce platform

---

## 🔧 Installation

### Step 1: Install Python Dependencies

Open Command Prompt and navigate to the sync-agent folder:

```powershell
cd C:\ecommerce-platform\sync-agent
pip install -r requirements.txt
```

### Step 2: Configure Connection

Copy the example configuration:

```powershell
copy .env.example .env
```

Edit `.env` with your settings (see Configuration section below).

---

## ⚙️ Configuration

### Method 1: MySQL Database (Recommended)

If KasaPOS uses MySQL database:

```env
KASAPOS_CONNECTION_TYPE=mysql
KASAPOS_MYSQL_HOST=localhost
KASAPOS_MYSQL_PORT=3306
KASAPOS_MYSQL_USER=root
KASAPOS_MYSQL_PASSWORD=your-kasapos-password
KASAPOS_MYSQL_DATABASE=kasapos
```

**Finding KasaPOS Database Settings:**
1. Open KasaPOS software
2. Go to Settings > Database
3. Note the host, port, username, and database name

### Method 2: SQLite Database

If KasaPOS uses SQLite:

```env
KASAPOS_CONNECTION_TYPE=sqlite
KASAPOS_SQLITE_PATH=C:\KasaPOS\data\kasapos.db
```

**Finding SQLite File:**
- Usually in `C:\KasaPOS\data\` or `C:\Program Files\KasaPOS\data\`
- Look for `.db` or `.sqlite` file

### Method 3: CSV Export

If you export data from KasaPOS:

```env
KASAPOS_CONNECTION_TYPE=csv
KASAPOS_EXPORT_FOLDER=C:\KasaPOS\exports
KASAPOS_PRODUCTS_FILE=products.csv
KASAPOS_INVENTORY_FILE=inventory.csv
KASAPOS_ORDERS_FILE=sales.csv
```

**Setting Up Auto-Export in KasaPOS:**
1. Open KasaPOS
2. Go to Reports > Export
3. Set up scheduled export to the folder

---

## 🧪 Testing Connection

Before running sync, test your connection:

```powershell
python kasapos_sync.py --test
```

Expected output:
```
🔍 Testing connections...

1. Testing KasaPOS connection...
   ✅ KasaPOS: Connected
   📦 Products found: 1234

2. Testing E-Commerce API...
   ✅ E-Commerce API: Connected
```

---

## 🚀 Running Sync

### One-Time Sync

For initial data sync or manual sync:

```powershell
# Full sync (all products)
python kasapos_sync.py --sync-once --sync-type full

# Delta sync (only changed products)
python kasapos_sync.py --sync-once --sync-type delta

# Inventory only (just stock levels)
python kasapos_sync.py --sync-once --sync-type inventory_only
```

### Continuous Sync (Recommended)

For automatic synchronization:

```powershell
python kasapos_sync.py --continuous
```

This will:
- Sync inventory every 1 minute during business hours (9 AM - 10 PM)
- Sync products every 5 minutes
- Full sync at 3 AM daily
- Sync sales every hour

### Run as Windows Service

To run sync agent automatically on startup:

1. Create a batch file `start_sync.bat`:
```batch
@echo off
cd C:\ecommerce-platform\sync-agent
python kasapos_sync.py --continuous
```

2. Add to Windows Task Scheduler:
   - Open Task Scheduler
   - Create Basic Task
   - Trigger: "When computer starts"
   - Action: Start a program
   - Program: `C:\ecommerce-platform\sync-agent\start_sync.bat`

---

## 📊 KasaPOS Database Schema

The sync agent expects these tables in KasaPOS:

### Products Table (`tbl_products`)
| Column | Description |
|--------|-------------|
| product_id | Primary key |
| product_code | SKU/Item code |
| product_name | Product name |
| mrp | Maximum retail price |
| selling_price | Your selling price |
| barcode | Barcode/EAN |
| category_id | Category reference |
| hsn_code | HSN code for GST |
| gst_rate | GST percentage |
| is_active | Active flag |
| updated_at | Last update timestamp |

### Stock Table (`tbl_stock`)
| Column | Description |
|--------|-------------|
| product_id | Product reference |
| quantity | Current stock |
| updated_at | Last update |

### Categories Table (`tbl_category`)
| Column | Description |
|--------|-------------|
| category_id | Primary key |
| category_name | Category name |

> **Note:** Column names may vary based on your KasaPOS version. 
> Edit `kasapos_adapter.py` if your schema is different.

---

## 🛠️ Customizing for Your KasaPOS Version

If your KasaPOS uses different table/column names, edit `kasapos_adapter.py`:

```python
class KasaPOSAdapter:
    # Change these to match your KasaPOS
    PRODUCT_TABLE = "your_products_table"
    INVENTORY_TABLE = "your_stock_table"
    SALES_TABLE = "your_sales_table"
    CATEGORY_TABLE = "your_category_table"
```

---

## 📱 Sync Features

### What Gets Synced

| Data | Direction | Frequency |
|------|-----------|-----------|
| Products | KasaPOS → Platform | Every 5 min |
| Inventory | KasaPOS → Platform | Every 1 min |
| Prices | KasaPOS → Platform | Every 5 min |
| Categories | KasaPOS → Platform | Every 5 min |
| Orders | Platform → KasaPOS | Coming soon |

### Sync Types

1. **Full Sync** - All products (use for initial setup)
2. **Delta Sync** - Only changed products (regular updates)
3. **Inventory Only** - Just stock levels (fastest)

---

## ❓ Troubleshooting

### "Connection Failed" Error

1. Check if KasaPOS is running
2. Verify database credentials
3. Check firewall settings
4. Try connecting manually:
   ```powershell
   mysql -h localhost -u root -p kasapos
   ```

### "No Products Found"

1. Verify table names match your KasaPOS version
2. Check if products are marked as active
3. Run with debug logging:
   ```powershell
   python kasapos_sync.py --test
   ```

### "API Connection Failed"

1. Check internet connection
2. Verify Store ID and API Key
3. Try accessing the API URL in browser

### Products Not Updating

1. Check `updated_at` column in KasaPOS
2. Ensure products have changes since last sync
3. Try full sync: `--sync-type full`

---

## 📞 Support

For help, contact:
- **Platform Support:** support@yourplatform.com
- **KasaPOS Support:** support@kasapos.com

---

## 📝 Changelog

- **v1.0.0** - Initial release with MySQL, SQLite, CSV support
