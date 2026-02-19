"""004_performance — pg_trgm, query indexes, BRIN on orders

This migration installs the pg_trgm extension and creates a set of composite
and partial indexes that align with the query patterns produced by the
storefront and admin endpoints.

Every DDL statement uses CONCURRENTLY so it can run against a live database
without taking an exclusive lock.  Alembic will execute these inside an
implicit transaction for the whole migration; if you need to run CONCURRENTLY
outside a transaction block, apply the statements manually or set
``transaction_per_migration = False`` in alembic.ini.

Revision ID: 004_performance
Revises: 003_security
"""
from alembic import op

revision = "004_performance"
down_revision = "003_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── pg_trgm — enables GIN trigram indexes for fast ILIKE ─────────────────
    # Required for sub-millisecond ILIKE '%term%' on large product tables.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── Product full-text / search indexes ───────────────────────────────────
    # Accelerates OR-based ILIKE searches across name/description.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_name_trgm "
        "ON products USING gin(name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_desc_trgm "
        "ON products USING gin(description gin_trgm_ops)"
    )

    # ── Product listing / filter indexes ─────────────────────────────────────
    # Covers the most common listing query:
    #   WHERE store_id=? AND category_id=? AND is_active=true
    #   ORDER BY selling_price [ASC|DESC]
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_store_cat_active_price "
        "ON products(store_id, category_id, is_active, selling_price)"
    )

    # Partial index — featured products widget (very selective, tiny index)
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_store_featured "
        "ON products(store_id, selling_price) "
        "WHERE is_featured = true AND is_active = true"
    )

    # In-stock filter + price range
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_store_instock_price "
        "ON products(store_id, selling_price) "
        "WHERE is_in_stock = true AND is_active = true"
    )

    # ── Order indexes ─────────────────────────────────────────────────────────
    # BRIN is tiny and efficient for the mostly-append-only orders table —
    # it records min/max created_at per 128-page block.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_created_brin "
        "ON orders USING brin(created_at)"
    )

    # Covering index for the admin dashboard query:
    #   WHERE store_id=? AND order_status=?
    #   ORDER BY created_at DESC
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_store_status_date "
        "ON orders(store_id, order_status, created_at DESC)"
    )

    # Customer order history (used on the storefront "My Orders" page)
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_store_date "
        "ON orders(user_id, store_id, created_at DESC) "
        "WHERE user_id IS NOT NULL"
    )

    # ── Category index ────────────────────────────────────────────────────────
    # Speeds up the storefront category tree query with display_order sort.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_categories_store_active_order "
        "ON categories(store_id, is_active, display_order)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_products_name_trgm")
    op.execute("DROP INDEX IF EXISTS idx_products_desc_trgm")
    op.execute("DROP INDEX IF EXISTS idx_products_store_cat_active_price")
    op.execute("DROP INDEX IF EXISTS idx_products_store_featured")
    op.execute("DROP INDEX IF EXISTS idx_products_store_instock_price")
    op.execute("DROP INDEX IF EXISTS idx_orders_created_brin")
    op.execute("DROP INDEX IF EXISTS idx_orders_store_status_date")
    op.execute("DROP INDEX IF EXISTS idx_orders_user_store_date")
    op.execute("DROP INDEX IF EXISTS idx_categories_store_active_order")
    # Note: we intentionally leave pg_trgm installed — removing an extension
    # is destructive and other schemas may depend on it.
