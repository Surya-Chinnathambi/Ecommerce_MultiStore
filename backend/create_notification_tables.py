"""
Create notification tables in the database
Run this script to create notification_templates, notifications, notification_preferences, and notification_logs tables
"""
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_notification_tables():
    """Create notification tables"""
    print("Creating notification tables...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if tables already exist
        check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('notification_templates', 'notifications', 'notification_preferences', 'notification_logs')
        """)
        
        existing_tables = [row[0] for row in conn.execute(check_query)]
        
        if existing_tables:
            print(f"⚠️  Found existing tables: {', '.join(existing_tables)}")
            response = input("Do you want to drop and recreate them? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborting...")
                return
            
            # Drop existing tables
            for table in ['notification_logs', 'notifications', 'notification_preferences', 'notification_templates']:
                if table in existing_tables:
                    print(f"Dropping table: {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            conn.commit()
        
        # Create notification_templates table
        print("Creating notification_templates table...")
        conn.execute(text("""
            CREATE TABLE notification_templates (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                subject VARCHAR(500),
                body_template TEXT NOT NULL,
                sms_template TEXT,
                variables JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(tenant_id, name)
            )
        """))
        
        # Create notifications table
        print("Creating notifications table...")
        conn.execute(text("""
            CREATE TABLE notifications (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                template_id INTEGER,
                notification_type VARCHAR(50) NOT NULL,
                priority VARCHAR(50) DEFAULT 'normal',
                subject VARCHAR(500) NOT NULL,
                body TEXT NOT NULL,
                data JSONB DEFAULT '{}',
                status VARCHAR(50) DEFAULT 'pending',
                read BOOLEAN DEFAULT false,
                clicked BOOLEAN DEFAULT false,
                read_at TIMESTAMP,
                clicked_at TIMESTAMP,
                sent_at TIMESTAMP,
                delivered_at TIMESTAMP,
                failed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                schedule_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES notification_templates(id) ON DELETE SET NULL
            )
        """))
        
        # Create notification_preferences table
        print("Creating notification_preferences table...")
        conn.execute(text("""
            CREATE TABLE notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                email_enabled BOOLEAN DEFAULT true,
                sms_enabled BOOLEAN DEFAULT true,
                push_enabled BOOLEAN DEFAULT true,
                in_app_enabled BOOLEAN DEFAULT true,
                order_updates BOOLEAN DEFAULT true,
                payment_updates BOOLEAN DEFAULT true,
                shipping_updates BOOLEAN DEFAULT true,
                promotional BOOLEAN DEFAULT true,
                marketing BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(user_id, tenant_id)
            )
        """))
        
        # Create notification_logs table
        print("Creating notification_logs table...")
        conn.execute(text("""
            CREATE TABLE notification_logs (
                id SERIAL PRIMARY KEY,
                notification_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                event VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                message TEXT,
                meta_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE
            )
        """))
        
        # Create indexes
        print("Creating indexes...")
        
        # Templates indexes
        conn.execute(text("CREATE INDEX idx_notification_templates_tenant ON notification_templates(tenant_id)"))
        conn.execute(text("CREATE INDEX idx_notification_templates_type ON notification_templates(notification_type)"))
        
        # Notifications indexes
        conn.execute(text("CREATE INDEX idx_notifications_tenant ON notifications(tenant_id)"))
        conn.execute(text("CREATE INDEX idx_notifications_user ON notifications(user_id)"))
        conn.execute(text("CREATE INDEX idx_notifications_status ON notifications(status)"))
        conn.execute(text("CREATE INDEX idx_notifications_type ON notifications(notification_type)"))
        conn.execute(text("CREATE INDEX idx_notifications_read ON notifications(read)"))
        conn.execute(text("CREATE INDEX idx_notifications_created ON notifications(created_at DESC)"))
        conn.execute(text("CREATE INDEX idx_notifications_schedule ON notifications(schedule_at)"))
        
        # Preferences indexes
        conn.execute(text("CREATE INDEX idx_notification_preferences_user ON notification_preferences(user_id)"))
        conn.execute(text("CREATE INDEX idx_notification_preferences_tenant ON notification_preferences(tenant_id)"))
        
        # Logs indexes
        conn.execute(text("CREATE INDEX idx_notification_logs_notification ON notification_logs(notification_id)"))
        conn.execute(text("CREATE INDEX idx_notification_logs_tenant ON notification_logs(tenant_id)"))
        conn.execute(text("CREATE INDEX idx_notification_logs_event ON notification_logs(event)"))
        
        conn.commit()
        
        print("\n✅ Notification tables created successfully!")
        print("\nCreated tables:")
        print("  - notification_templates")
        print("  - notifications")
        print("  - notification_preferences")
        print("  - notification_logs")
        print("\nCreated indexes for optimal query performance")

if __name__ == "__main__":
    try:
        create_notification_tables()
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        sys.exit(1)
