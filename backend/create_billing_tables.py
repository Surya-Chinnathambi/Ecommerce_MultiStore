"""
Create billing integration tables in the database
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_billing_tables():
    """Create billing integration tables"""
    print("Creating billing integration tables...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if tables already exist
        check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('billing_integrations', 'billing_sync_logs', 'invoice_exports', 'product_imports', 'csv_templates')
        """)
        
        existing_tables = [row[0] for row in conn.execute(check_query)]
        
        if existing_tables:
            print(f"⚠️  Found existing tables: {', '.join(existing_tables)}")
            response = input("Do you want to drop and recreate them? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborting...")
                return
            
            # Drop existing tables in correct order
            for table in ['product_imports', 'invoice_exports', 'billing_sync_logs', 'csv_templates', 'billing_integrations']:
                if table in existing_tables:
                    print(f"Dropping table: {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            conn.commit()
        
        # Create billing_integrations table
        print("Creating billing_integrations table...")
        conn.execute(text("""
            CREATE TABLE billing_integrations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                provider VARCHAR(50) NOT NULL,
                config JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                auto_sync BOOLEAN DEFAULT false,
                sync_direction VARCHAR(50) DEFAULT 'push',
                sync_frequency_minutes INTEGER DEFAULT 60,
                sync_entities JSONB DEFAULT '[]',
                field_mapping JSONB DEFAULT '{}',
                last_sync_at TIMESTAMP,
                last_sync_status VARCHAR(50),
                last_sync_message TEXT,
                total_syncs INTEGER DEFAULT 0,
                successful_syncs INTEGER DEFAULT 0,
                failed_syncs INTEGER DEFAULT 0,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create billing_sync_logs table
        print("Creating billing_sync_logs table...")
        conn.execute(text("""
            CREATE TABLE billing_sync_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                integration_id UUID NOT NULL REFERENCES billing_integrations(id) ON DELETE CASCADE,
                store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                sync_type VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                direction VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL,
                records_processed INTEGER DEFAULT 0,
                records_succeeded INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                records_skipped INTEGER DEFAULT 0,
                summary TEXT,
                error_message TEXT,
                details JSONB DEFAULT '{}',
                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                duration_seconds INTEGER,
                triggered_by UUID REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create invoice_exports table
        print("Creating invoice_exports table...")
        conn.execute(text("""
            CREATE TABLE invoice_exports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                integration_id UUID REFERENCES billing_integrations(id) ON DELETE SET NULL,
                store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                invoice_number VARCHAR(100) NOT NULL,
                external_id VARCHAR(200),
                provider VARCHAR(50) NOT NULL,
                invoice_data JSONB DEFAULT '{}',
                export_format VARCHAR(50) DEFAULT 'json',
                status VARCHAR(50) DEFAULT 'pending',
                exported_at TIMESTAMP,
                synced_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                file_path VARCHAR(500),
                file_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create product_imports table
        print("Creating product_imports table...")
        conn.execute(text("""
            CREATE TABLE product_imports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_id UUID REFERENCES products(id) ON DELETE SET NULL,
                integration_id UUID REFERENCES billing_integrations(id) ON DELETE SET NULL,
                store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                external_id VARCHAR(200) NOT NULL,
                external_sku VARCHAR(100),
                provider VARCHAR(50) NOT NULL,
                product_data JSONB DEFAULT '{}',
                import_format VARCHAR(50) DEFAULT 'json',
                field_mappings JSONB DEFAULT '{}',
                status VARCHAR(50) DEFAULT 'pending',
                imported_at TIMESTAMP,
                processed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create csv_templates table
        print("Creating csv_templates table...")
        conn.execute(text("""
            CREATE TABLE csv_templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                direction VARCHAR(50) NOT NULL,
                column_mappings JSONB DEFAULT '{}',
                delimiter VARCHAR(1) DEFAULT ',',
                has_header BOOLEAN DEFAULT true,
                encoding VARCHAR(20) DEFAULT 'utf-8',
                template_file VARCHAR(500),
                sample_file VARCHAR(500),
                is_default BOOLEAN DEFAULT false,
                is_active BOOLEAN DEFAULT true,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes
        print("Creating indexes...")
        
        # Integrations indexes
        conn.execute(text("CREATE INDEX idx_billing_integrations_store ON billing_integrations(store_id)"))
        conn.execute(text("CREATE INDEX idx_billing_integrations_provider ON billing_integrations(provider)"))
        conn.execute(text("CREATE INDEX idx_billing_integrations_active ON billing_integrations(is_active)"))
        
        # Sync logs indexes
        conn.execute(text("CREATE INDEX idx_billing_sync_logs_integration ON billing_sync_logs(integration_id)"))
        conn.execute(text("CREATE INDEX idx_billing_sync_logs_store ON billing_sync_logs(store_id)"))
        conn.execute(text("CREATE INDEX idx_billing_sync_logs_status ON billing_sync_logs(status)"))
        conn.execute(text("CREATE INDEX idx_billing_sync_logs_created ON billing_sync_logs(created_at DESC)"))
        
        # Invoice exports indexes
        conn.execute(text("CREATE INDEX idx_invoice_exports_order ON invoice_exports(order_id)"))
        conn.execute(text("CREATE INDEX idx_invoice_exports_integration ON invoice_exports(integration_id)"))
        conn.execute(text("CREATE INDEX idx_invoice_exports_store ON invoice_exports(store_id)"))
        conn.execute(text("CREATE INDEX idx_invoice_exports_status ON invoice_exports(status)"))
        conn.execute(text("CREATE INDEX idx_invoice_exports_invoice_number ON invoice_exports(invoice_number)"))
        
        # Product imports indexes
        conn.execute(text("CREATE INDEX idx_product_imports_product ON product_imports(product_id)"))
        conn.execute(text("CREATE INDEX idx_product_imports_integration ON product_imports(integration_id)"))
        conn.execute(text("CREATE INDEX idx_product_imports_store ON product_imports(store_id)"))
        conn.execute(text("CREATE INDEX idx_product_imports_status ON product_imports(status)"))
        conn.execute(text("CREATE INDEX idx_product_imports_external_id ON product_imports(external_id)"))
        
        # CSV templates indexes
        conn.execute(text("CREATE INDEX idx_csv_templates_store ON csv_templates(store_id)"))
        conn.execute(text("CREATE INDEX idx_csv_templates_entity_type ON csv_templates(entity_type)"))
        
        conn.commit()
        
        print("\n✅ Billing integration tables created successfully!")
        print("\nCreated tables:")
        print("  - billing_integrations")
        print("  - billing_sync_logs")
        print("  - invoice_exports")
        print("  - product_imports")
        print("  - csv_templates")
        print("\nCreated indexes for optimal query performance")

if __name__ == "__main__":
    try:
        create_billing_tables()
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        sys.exit(1)
