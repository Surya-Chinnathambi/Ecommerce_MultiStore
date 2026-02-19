"""marketplace_tables

Revision ID: 002_marketplace
Revises: 001_initial
Create Date: 2026-02-18

Adds:
  - product_variant_groups
  - product_variants
  - wishlist_items
  - sellers
  - seller_products
  - seller_payouts
  - return_requests
  - return_items
  - coupons
  - coupon_usages
  - pincode_delivery
  - coupon_id / coupon_code columns on orders
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_marketplace'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # ── product_variant_groups ──────────────────────────────────────────────
    op.create_table(
        'product_variant_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('variant_type', sa.String(50), default='custom'),
        sa.Column('display_order', sa.Integer, default=0),
    )
    op.create_index('idx_pvg_product', 'product_variant_groups', ['product_id'])

    # ── product_variants ────────────────────────────────────────────────────
    op.create_table(
        'product_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('product_variant_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('value', sa.String(100), nullable=False),
        sa.Column('display_label', sa.String(100)),
        sa.Column('color_hex', sa.String(7)),
        sa.Column('mrp', sa.Float),
        sa.Column('selling_price', sa.Float),
        sa.Column('discount_pct', sa.Float),
        sa.Column('sku', sa.String(100)),
        sa.Column('quantity', sa.Integer, default=0),
        sa.Column('is_in_stock', sa.Boolean, default=True),
        sa.Column('images', postgresql.JSONB, default=[]),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('product_id', 'group_id', 'value', name='uq_variant_value'),
    )
    op.create_index('idx_pv_product_active', 'product_variants', ['product_id', 'is_active'])
    op.create_index('idx_pv_sku', 'product_variants', ['sku'])

    # ── wishlist_items ──────────────────────────────────────────────────────
    op.create_table(
        'wishlist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('added_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_wishlist_user_product'),
    )
    op.create_index('idx_wishlist_user', 'wishlist_items', ['user_id'])
    op.create_index('idx_wishlist_store', 'wishlist_items', ['store_id'])

    # ── sellers ─────────────────────────────────────────────────────────────
    op.create_table(
        'sellers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_name', sa.String(300), nullable=False),
        sa.Column('business_type', sa.String(50)),
        sa.Column('gstin', sa.String(20)),
        sa.Column('pan', sa.String(20)),
        sa.Column('fssai_number', sa.String(20)),
        sa.Column('address_line1', sa.String(300)),
        sa.Column('address_line2', sa.String(300)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(100)),
        sa.Column('pincode', sa.String(10)),
        sa.Column('bank_account_number', sa.String(50)),
        sa.Column('bank_ifsc', sa.String(20)),
        sa.Column('bank_account_name', sa.String(200)),
        sa.Column('upi_id', sa.String(100)),
        sa.Column('commission_rate', sa.Float, default=5.0),
        sa.Column('payout_cycle_days', sa.Integer, default=7),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('kyc_verified', sa.Boolean, default=False),
        sa.Column('kyc_documents', postgresql.JSONB, default=[]),
        sa.Column('avg_rating', sa.Float, default=0.0),
        sa.Column('total_ratings', sa.Integer, default=0),
        sa.Column('total_orders', sa.Integer, default=0),
        sa.Column('total_returns', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('approved_at', sa.DateTime),
    )
    op.create_index('idx_seller_status', 'sellers', ['status', 'is_active'])

    # ── seller_products ─────────────────────────────────────────────────────
    op.create_table(
        'seller_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selling_price', sa.Float, nullable=False),
        sa.Column('mrp', sa.Float, nullable=False),
        sa.Column('quantity', sa.Integer, default=0),
        sa.Column('is_in_stock', sa.Boolean, default=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('dispatch_days', sa.Integer, default=2),
        sa.Column('return_days', sa.Integer, default=7),
        sa.Column('warranty_months', sa.Integer, default=0),
        sa.Column('display_rank', sa.Integer, default=100),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('seller_id', 'product_id', name='uq_seller_product'),
    )
    op.create_index('idx_sp_product_active', 'seller_products', ['product_id', 'is_active'])

    # ── seller_payouts ──────────────────────────────────────────────────────
    op.create_table(
        'seller_payouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('period_start', sa.DateTime, nullable=False),
        sa.Column('period_end', sa.DateTime, nullable=False),
        sa.Column('gross_amount', sa.Float, default=0.0),
        sa.Column('commission', sa.Float, default=0.0),
        sa.Column('refund_deductions', sa.Float, default=0.0),
        sa.Column('net_amount', sa.Float, default=0.0),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('payment_ref', sa.String(100)),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('paid_at', sa.DateTime),
        sa.Column('orders_count', sa.Integer, default=0),
        sa.Column('returns_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # ── coupons ─────────────────────────────────────────────────────────────
    op.create_table(
        'coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('coupon_type', sa.String(20), nullable=False, default='percent'),
        sa.Column('discount_value', sa.Float, nullable=False),
        sa.Column('max_discount_cap', sa.Float),
        sa.Column('buy_quantity', sa.Integer),
        sa.Column('get_quantity', sa.Integer),
        sa.Column('min_order_amount', sa.Float, default=0.0),
        sa.Column('max_uses_total', sa.Integer),
        sa.Column('max_uses_per_user', sa.Integer, default=1),
        sa.Column('applicable_category_ids', postgresql.JSONB, default=[]),
        sa.Column('applicable_product_ids', postgresql.JSONB, default=[]),
        sa.Column('valid_from', sa.DateTime, nullable=False),
        sa.Column('valid_until', sa.DateTime, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('used_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('store_id', 'code', name='uq_coupon_store_code'),
    )
    op.create_index('idx_coupon_store_active', 'coupons', ['store_id', 'is_active'])
    op.create_index('idx_coupon_valid_until', 'coupons', ['valid_until'])

    # ── coupon_usages ────────────────────────────────────────────────────────
    op.create_table(
        'coupon_usages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('coupon_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('coupons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('orders.id', ondelete='SET NULL')),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('discount_applied', sa.Float, nullable=False),
        sa.Column('used_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_cu_coupon_user', 'coupon_usages', ['coupon_id', 'user_id'])

    # ── return_requests ──────────────────────────────────────────────────────
    op.create_table(
        'return_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('orders.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('return_number', sa.String(50), nullable=False, unique=True),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('images', postgresql.JSONB, default=[]),
        sa.Column('status', sa.String(30), default='requested'),
        sa.Column('admin_notes', sa.Text),
        sa.Column('rejection_reason', sa.Text),
        sa.Column('pickup_scheduled_at', sa.DateTime),
        sa.Column('pickup_completed_at', sa.DateTime),
        sa.Column('tracking_id', sa.String(100)),
        sa.Column('refund_amount', sa.Float),
        sa.Column('refund_method', sa.String(50)),
        sa.Column('refund_ref', sa.String(100)),
        sa.Column('refunded_at', sa.DateTime),
        sa.Column('requested_at', sa.DateTime, nullable=False),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    op.create_index('idx_return_order', 'return_requests', ['order_id'])
    op.create_index('idx_return_store_status', 'return_requests', ['store_id', 'status'])
    op.create_index('idx_return_user', 'return_requests', ['user_id'])

    # ── return_items ─────────────────────────────────────────────────────────
    op.create_table(
        'return_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('return_request_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('return_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_item_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('order_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Float, nullable=False),
        sa.Column('refund_amount', sa.Float),
    )
    op.create_index('idx_ri_return_request', 'return_items', ['return_request_id'])

    # ── pincode_delivery ──────────────────────────────────────────────────────
    op.create_table(
        'pincode_delivery',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pincode', sa.String(10), nullable=False),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(100)),
        sa.Column('is_serviceable', sa.Boolean, default=True),
        sa.Column('standard_days', sa.Integer, default=5),
        sa.Column('express_days', sa.Integer),
        sa.Column('same_day', sa.Boolean, default=False),
        sa.Column('cod_available', sa.Boolean, default=True),
        sa.Column('prepaid_only', sa.Boolean, default=False),
        sa.Column('courier_partner', sa.String(100)),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('store_id', 'pincode', name='uq_pincode_store'),
    )
    op.create_index('idx_pincode_serviceable', 'pincode_delivery', ['store_id', 'is_serviceable'])

    # ── add coupon columns to orders ─────────────────────────────────────────
    op.add_column('orders', sa.Column('coupon_code', sa.String(50), index=True))
    op.add_column('orders', sa.Column('coupon_id', postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey('coupons.id', ondelete='SET NULL'),
                                       nullable=True))


def downgrade():
    op.drop_column('orders', 'coupon_id')
    op.drop_column('orders', 'coupon_code')
    op.drop_table('pincode_delivery')
    op.drop_table('return_items')
    op.drop_table('return_requests')
    op.drop_table('coupon_usages')
    op.drop_table('coupons')
    op.drop_table('seller_payouts')
    op.drop_table('seller_products')
    op.drop_table('sellers')
    op.drop_table('wishlist_items')
    op.drop_table('product_variants')
    op.drop_table('product_variant_groups')
