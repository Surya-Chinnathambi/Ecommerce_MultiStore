"""
CSV/Excel Import/Export Service
Handles data import/export for legacy systems
"""
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class CSVService:
    """Service for CSV/Excel import and export"""
    
    @staticmethod
    def export_invoices_to_csv(
        invoices: List[Dict[str, Any]],
        template: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Export invoices to CSV format
        
        Args:
            invoices: List of invoice dictionaries
            template: Column mapping template
        
        Returns:
            CSV string
        """
        if not invoices:
            return ""
        
        # Default column mappings
        default_columns = {
            'invoice_number': 'Invoice Number',
            'order_id': 'Order ID',
            'customer_name': 'Customer Name',
            'customer_email': 'Customer Email',
            'date': 'Invoice Date',
            'due_date': 'Due Date',
            'subtotal': 'Subtotal',
            'tax': 'Tax',
            'shipping': 'Shipping',
            'total': 'Total',
            'status': 'Status',
            'payment_method': 'Payment Method'
        }
        
        columns = template or default_columns
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns.values())
        writer.writeheader()
        
        for invoice in invoices:
            row = {}
            for key, header in columns.items():
                row[header] = invoice.get(key, '')
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_products_to_csv(
        products: List[Dict[str, Any]],
        template: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Export products to CSV format
        
        Args:
            products: List of product dictionaries
            template: Column mapping template
        
        Returns:
            CSV string
        """
        if not products:
            return ""
        
        # Default column mappings
        default_columns = {
            'sku': 'SKU',
            'name': 'Product Name',
            'description': 'Description',
            'price': 'Price',
            'cost': 'Cost',
            'quantity': 'Quantity',
            'category': 'Category',
            'brand': 'Brand',
            'barcode': 'Barcode',
            'weight': 'Weight',
            'dimensions': 'Dimensions',
            'tax_rate': 'Tax Rate',
            'status': 'Status'
        }
        
        columns = template or default_columns
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns.values())
        writer.writeheader()
        
        for product in products:
            row = {}
            for key, header in columns.items():
                row[header] = product.get(key, '')
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_customers_to_csv(
        customers: List[Dict[str, Any]],
        template: Optional[Dict[str, str]] = None
    ) -> str:
        """Export customers to CSV format"""
        if not customers:
            return ""
        
        default_columns = {
            'id': 'Customer ID',
            'name': 'Name',
            'email': 'Email',
            'phone': 'Phone',
            'company': 'Company',
            'address': 'Address',
            'city': 'City',
            'state': 'State',
            'zip': 'ZIP Code',
            'country': 'Country',
            'total_orders': 'Total Orders',
            'total_spent': 'Total Spent',
            'created_at': 'Customer Since'
        }
        
        columns = template or default_columns
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns.values())
        writer.writeheader()
        
        for customer in customers:
            row = {}
            for key, header in columns.items():
                row[header] = customer.get(key, '')
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def import_products_from_csv(
        csv_content: str,
        template: Optional[Dict[str, str]] = None,
        has_header: bool = True,
        delimiter: str = ','
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Import products from CSV
        
        Args:
            csv_content: CSV file content
            template: Column mapping (CSV column -> system field)
            has_header: Whether CSV has header row
            delimiter: CSV delimiter
        
        Returns:
            Tuple of (products, errors)
        """
        products = []
        errors = []
        
        # Default reverse mapping (CSV header -> system field)
        default_mapping = {
            'SKU': 'sku',
            'Product Name': 'name',
            'Description': 'description',
            'Price': 'price',
            'Cost': 'cost',
            'Quantity': 'quantity',
            'Category': 'category',
            'Brand': 'brand'
        }
        
        mapping = template or default_mapping
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file, delimiter=delimiter) if has_header else csv.reader(csv_file, delimiter=delimiter)
            
            for idx, row in enumerate(reader, start=1):
                try:
                    product = {}
                    
                    if has_header:
                        # Map CSV columns to system fields
                        for csv_col, sys_field in mapping.items():
                            if csv_col in row:
                                value = row[csv_col].strip()
                                
                                # Type conversion
                                if sys_field in ['price', 'cost']:
                                    product[sys_field] = float(value) if value else 0.0
                                elif sys_field == 'quantity':
                                    product[sys_field] = int(value) if value else 0
                                else:
                                    product[sys_field] = value
                    else:
                        # No header - use positional mapping
                        product['sku'] = row[0] if len(row) > 0 else ''
                        product['name'] = row[1] if len(row) > 1 else ''
                        product['price'] = float(row[2]) if len(row) > 2 and row[2] else 0.0
                        product['quantity'] = int(row[3]) if len(row) > 3 and row[3] else 0
                    
                    # Validation
                    if not product.get('sku'):
                        errors.append({'row': idx, 'error': 'Missing SKU'})
                        continue
                    
                    if not product.get('name'):
                        errors.append({'row': idx, 'error': 'Missing product name'})
                        continue
                    
                    products.append(product)
                
                except Exception as e:
                    errors.append({'row': idx, 'error': str(e)})
            
            logger.info(f"CSV import: {len(products)} products, {len(errors)} errors")
            return products, errors
        
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            return [], [{'row': 0, 'error': f'CSV parsing failed: {str(e)}'}]
    
    @staticmethod
    def import_customers_from_csv(
        csv_content: str,
        template: Optional[Dict[str, str]] = None,
        has_header: bool = True,
        delimiter: str = ','
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """Import customers from CSV"""
        customers = []
        errors = []
        
        default_mapping = {
            'Name': 'name',
            'Email': 'email',
            'Phone': 'phone',
            'Company': 'company',
            'Address': 'address',
            'City': 'city',
            'State': 'state',
            'ZIP Code': 'zip',
            'Country': 'country'
        }
        
        mapping = template or default_mapping
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            for idx, row in enumerate(reader, start=1):
                try:
                    customer = {}
                    
                    for csv_col, sys_field in mapping.items():
                        if csv_col in row:
                            customer[sys_field] = row[csv_col].strip()
                    
                    # Validation
                    if not customer.get('email'):
                        errors.append({'row': idx, 'error': 'Missing email'})
                        continue
                    
                    customers.append(customer)
                
                except Exception as e:
                    errors.append({'row': idx, 'error': str(e)})
            
            return customers, errors
        
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            return [], [{'row': 0, 'error': f'CSV parsing failed: {str(e)}'}]
    
    @staticmethod
    def generate_sample_csv(entity_type: str) -> str:
        """Generate sample CSV template"""
        samples = {
            'product': [
                {'SKU': 'PROD-001', 'Product Name': 'Sample Product', 'Description': 'Product description', 
                 'Price': '99.99', 'Cost': '50.00', 'Quantity': '100', 'Category': 'Electronics', 'Brand': 'BrandName'},
                {'SKU': 'PROD-002', 'Product Name': 'Another Product', 'Description': 'Another description', 
                 'Price': '149.99', 'Cost': '75.00', 'Quantity': '50', 'Category': 'Accessories', 'Brand': 'BrandName'}
            ],
            'invoice': [
                {'Invoice Number': 'INV-001', 'Order ID': 'ORD-001', 'Customer Name': 'John Doe', 
                 'Customer Email': 'john@example.com', 'Invoice Date': '2025-01-15', 'Subtotal': '100.00',
                 'Tax': '10.00', 'Shipping': '5.00', 'Total': '115.00', 'Status': 'paid'},
                {'Invoice Number': 'INV-002', 'Order ID': 'ORD-002', 'Customer Name': 'Jane Smith',
                 'Customer Email': 'jane@example.com', 'Invoice Date': '2025-01-16', 'Subtotal': '200.00',
                 'Tax': '20.00', 'Shipping': '10.00', 'Total': '230.00', 'Status': 'pending'}
            ],
            'customer': [
                {'Customer ID': 'CUST-001', 'Name': 'John Doe', 'Email': 'john@example.com',
                 'Phone': '+1234567890', 'Company': 'Acme Corp', 'Address': '123 Main St',
                 'City': 'New York', 'State': 'NY', 'ZIP Code': '10001', 'Country': 'USA'},
                {'Customer ID': 'CUST-002', 'Name': 'Jane Smith', 'Email': 'jane@example.com',
                 'Phone': '+1234567891', 'Company': 'Tech Inc', 'Address': '456 Oak Ave',
                 'City': 'San Francisco', 'State': 'CA', 'ZIP Code': '94102', 'Country': 'USA'}
            ]
        }
        
        data = samples.get(entity_type, [])
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()


# Global CSV service instance
csv_service = CSVService()
