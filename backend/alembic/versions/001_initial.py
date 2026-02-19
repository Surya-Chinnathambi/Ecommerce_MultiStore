"""Initial migration - Complete schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-02-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stores table
    op.create_table(
        'stores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('owner_name', sa.String(200), nullable=True),
        sa.Column('owner_phone', sa.String(20), nullable=True),
        sa.Column('owner_email', sa.String(255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('pincode', sa.String(10), nullable=True),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('timezone', sa.String(50), server_default='Asia/Kolkata'),
        sa.Column('language', sa.String(10), server_default='en'),
        sa.Column('sync_tier', sa.Enum('tier1', 'tier2', 'tier3', 'tier4', name='storetier'), server_default='tier3'),
        sa.Column('sync_interval_minutes', sa.Integer(), server_default='30'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_api_key', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('active', 'trial', 'suspended', 'inactive', name='storestatus'), server_default='trial'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), server_default='#000000'),
        sa.Column('secondary_color', sa.String(7), server_default='#FFFFFF'),
        sa.Column('settings', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_store_slug', 'stores', ['slug'], unique=True)
    op.create_index('idx_store_external_id', 'stores', ['external_id'], unique=True)
    op.create_index('idx_store_domain', 'stores', ['domain'], unique=True)
    op.create_index('idx_store_status_tier', 'stores', ['status', 'sync_tier'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('customer', 'admin', 'super_admin', name='userrole'), server_default='customer'),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_email_verified', sa.Boolean(), server_default='false'),
        sa.Column('is_phone_verified', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('password_reset_token', sa.String(255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_user_phone', 'users', ['phone'], unique=True)
    
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_category_store_slug', 'categories', ['store_id', 'slug'], unique=True)
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mrp', sa.Float(), nullable=False),
        sa.Column('selling_price', sa.Float(), nullable=False),
        sa.Column('discount_percent', sa.Float(), server_default='0'),
        sa.Column('cost_price', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Integer(), server_default='0'),
        sa.Column('low_stock_threshold', sa.Integer(), server_default='10'),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('hsn_code', sa.String(20), nullable=True),
        sa.Column('gst_percent', sa.Float(), server_default='0'),
        sa.Column('images', postgresql.JSONB(), server_default='[]'),
        sa.Column('thumbnail', sa.String(500), nullable=True),
        sa.Column('meta_title', sa.String(200), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('meta_keywords', sa.String(500), nullable=True),
        sa.Column('attributes', postgresql.JSONB(), server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_featured', sa.Boolean(), server_default='false'),
        sa.Column('is_in_stock', sa.Boolean(), server_default='true'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_version', sa.Integer(), server_default='1'),
        sa.Column('sync_checksum', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_product_store_external', 'products', ['store_id', 'external_id'], unique=True)
    op.create_index('idx_product_store_active', 'products', ['store_id', 'is_active'])
    op.create_index('idx_product_store_stock', 'products', ['store_id', 'is_in_stock'])
    op.create_index('idx_product_sku', 'products', ['sku'])
    op.create_index('idx_product_barcode', 'products', ['barcode'])
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_number', sa.String(50), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_name', sa.String(200), nullable=False),
        sa.Column('customer_phone', sa.String(20), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('delivery_address', sa.Text(), nullable=False),
        sa.Column('delivery_city', sa.String(100), nullable=True),
        sa.Column('delivery_state', sa.String(100), nullable=True),
        sa.Column('delivery_pincode', sa.String(10), nullable=True),
        sa.Column('delivery_landmark', sa.String(200), nullable=True),
        sa.Column('order_status', sa.Enum('pending', 'confirmed', 'processing', 'ready', 'delivered', 'cancelled', name='orderstatus'), server_default='pending'),
        sa.Column('payment_status', sa.Enum('pending', 'cod', 'paid', 'failed', 'refunded', name='paymentstatus'), server_default='cod'),
        sa.Column('payment_method', sa.String(50), server_default='COD'),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), server_default='0'),
        sa.Column('discount_amount', sa.Float(), server_default='0'),
        sa.Column('delivery_charge', sa.Float(), server_default='0'),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('expected_delivery_date', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_order_number', 'orders', ['order_number'], unique=True)
    op.create_index('idx_order_store_status', 'orders', ['store_id', 'order_status'])
    op.create_index('idx_order_store_date', 'orders', ['store_id', 'created_at'])
    op.create_index('idx_order_user', 'orders', ['user_id'])
    
    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('product_sku', sa.String(100), nullable=True),
        sa.Column('product_image', sa.String(500), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('tax_percent', sa.Float(), server_default='0'),
        sa.Column('tax_amount', sa.Float(), server_default='0'),
        sa.Column('discount_amount', sa.Float(), server_default='0'),
        sa.Column('total', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_orderitem_order', 'order_items', ['order_id'])
    op.create_index('idx_orderitem_product', 'order_items', ['product_id'])
    
    # Create addresses table
    op.create_table(
        'addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('address_line1', sa.String(500), nullable=False),
        sa.Column('address_line2', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('pincode', sa.String(10), nullable=False),
        sa.Column('landmark', sa.String(255), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('address_type', sa.String(50), server_default='home'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payment_gateway', sa.Enum('stripe', 'razorpay', 'cod', 'manual', name='paymentgateway'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded', 'partially_refunded', name='payment_status'), server_default='pending'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('gateway_payment_id', sa.String(255), nullable=True),
        sa.Column('gateway_order_id', sa.String(255), nullable=True),
        sa.Column('gateway_signature', sa.String(500), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('card_last4', sa.String(4), nullable=True),
        sa.Column('card_brand', sa.String(20), nullable=True),
        sa.Column('transaction_fee', sa.Float(), server_default='0'),
        sa.Column('net_amount', sa.Float(), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('customer_name', sa.String(200), nullable=True),
        sa.Column('billing_address', postgresql.JSONB(), nullable=True),
        sa.Column('gateway_response', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('initiated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_payment_store_status', 'payments', ['store_id', 'status'])
    op.create_index('idx_payment_gateway_ref', 'payments', ['gateway_payment_id', 'gateway_order_id'])
    
    # Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sync_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('records_received', sa.Integer(), server_default='0'),
        sa.Column('records_created', sa.Integer(), server_default='0'),
        sa.Column('records_updated', sa.Integer(), server_default='0'),
        sa.Column('records_failed', sa.Integer(), server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_log_store_date', 'sync_logs', ['store_id', 'started_at'])
    
    # Create product_reviews table
    op.create_table(
        'product_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('images', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), server_default='false'),
        sa.Column('is_approved', sa.Boolean(), server_default='true'),
        sa.Column('is_featured', sa.Boolean(), server_default='false'),
        sa.Column('helpful_count', sa.Integer(), server_default='0'),
        sa.Column('not_helpful_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_review_product_rating', 'product_reviews', ['product_id', 'rating'])
    op.create_index('idx_review_store_approved', 'product_reviews', ['store_id', 'is_approved'])


def downgrade() -> None:
    op.drop_table('product_reviews')
    op.drop_table('sync_logs')
    op.drop_table('payments')
    op.drop_table('addresses')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')
    op.drop_table('stores')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS storetier')
    op.execute('DROP TYPE IF EXISTS storestatus')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS orderstatus')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymentgateway')
    op.execute('DROP TYPE IF EXISTS payment_status')
