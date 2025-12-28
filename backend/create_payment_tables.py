"""
Create payment tables migration
Run this to add payment, refund, and webhook tables
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def create_payment_tables():
    """Create payment-related tables in the database"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create payments table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                
                payment_gateway VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                
                amount FLOAT NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'INR',
                
                gateway_payment_id VARCHAR(255),
                gateway_order_id VARCHAR(255),
                gateway_signature VARCHAR(500),
                
                payment_method VARCHAR(50),
                card_last4 VARCHAR(4),
                card_brand VARCHAR(20),
                
                transaction_fee FLOAT DEFAULT 0.0,
                net_amount FLOAT,
                
                customer_email VARCHAR(255),
                customer_phone VARCHAR(20),
                customer_name VARCHAR(200),
                
                billing_address JSONB,
                gateway_response JSONB,
                error_message TEXT,
                error_code VARCHAR(50),
                
                metadata JSONB DEFAULT '{}',
                notes TEXT,
                
                initiated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP,
                failed_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))
        
        # Create indexes for payments
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_payment_store_status ON payments(store_id, status);
            CREATE INDEX IF NOT EXISTS idx_payment_order ON payments(order_id);
            CREATE INDEX IF NOT EXISTS idx_payment_gateway_ref_1 ON payments(gateway_payment_id);
            CREATE INDEX IF NOT EXISTS idx_payment_gateway_ref_2 ON payments(gateway_order_id);
            CREATE INDEX IF NOT EXISTS idx_payment_created ON payments(created_at);
        """))
        
        # Create refunds table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS refunds (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
                store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                amount FLOAT NOT NULL,
                currency VARCHAR(3) NOT NULL DEFAULT 'INR',
                reason TEXT,
                
                gateway_refund_id VARCHAR(255),
                gateway_response JSONB,
                
                initiated_by VARCHAR(100),
                approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
                
                error_message TEXT,
                error_code VARCHAR(50),
                
                metadata JSONB DEFAULT '{}',
                notes TEXT,
                
                initiated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP,
                failed_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))
        
        # Create indexes for refunds
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_refund_payment ON refunds(payment_id);
            CREATE INDEX IF NOT EXISTS idx_refund_store_status ON refunds(store_id, status);
            CREATE INDEX IF NOT EXISTS idx_refund_created ON refunds(created_at);
        """))
        
        # Create payment_webhooks table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_webhooks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                
                gateway VARCHAR(50) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                event_id VARCHAR(255) UNIQUE,
                
                payload JSONB NOT NULL,
                signature VARCHAR(500),
                
                processed BOOLEAN DEFAULT FALSE,
                processed_at TIMESTAMP,
                processing_error TEXT,
                retry_count INTEGER DEFAULT 0,
                
                payment_id UUID REFERENCES payments(id) ON DELETE SET NULL,
                
                received_at TIMESTAMP NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))
        
        # Create indexes for webhooks
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_webhook_gateway_event ON payment_webhooks(gateway, event_type);
            CREATE INDEX IF NOT EXISTS idx_webhook_processed ON payment_webhooks(processed, received_at);
            CREATE INDEX IF NOT EXISTS idx_webhook_event_id ON payment_webhooks(event_id);
        """))
        
        conn.commit()
        print("✅ Payment tables created successfully!")
        print("Tables: payments, refunds, payment_webhooks")

if __name__ == "__main__":
    create_payment_tables()
