"""005_advanced_features — user_product_views table + popularity_score column

Creates the user_product_views table for personalised recommendations and
recently-viewed history.  Also adds a popularity_score column to products
used by the search indexer.

Revision ID: 005_advanced_features
Revises: 004_performance
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "005_advanced_features"
down_revision = "004_performance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── user_product_views ────────────────────────────────────────────────────
    op.create_table(
        "user_product_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("view_count", sa.Integer(), default=1, server_default="1"),
        sa.Column("last_viewed_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"),
                  nullable=False),
    )

    # Indexes used by the recommendation service
    op.create_index("idx_upv_user_store",    "user_product_views", ["user_id",    "store_id"])
    op.create_index("idx_upv_session_store", "user_product_views", ["session_id", "store_id"])
    op.create_index("idx_upv_product_store", "user_product_views", ["product_id", "store_id"])
    op.create_index("idx_upv_last_viewed",   "user_product_views", ["last_viewed_at"])

    # ── popularity_score on products ─────────────────────────────────────────
    # Stores the computed score pushed by the Celery popularity-update task.
    op.add_column(
        "products",
        sa.Column("popularity_score", sa.Float(), nullable=True,
                  server_default="0.0"),
    )
    op.create_index(
        "idx_product_popularity",
        "products",
        ["store_id", "popularity_score"],
        postgresql_where=sa.text("is_active = true"),
    )

    # ── daily_analytics — add items_sold index ───────────────────────────────
    # Speeds up the revenue-by-category aggregation query.
    op.execute(
        "CREATE INDEX IF NOT EXISTS "
        "idx_order_items_product_created "
        "ON order_items (product_id) "
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_order_items_product_created")
    op.drop_index("idx_product_popularity", table_name="products")
    op.drop_column("products", "popularity_score")

    op.drop_index("idx_upv_last_viewed",   table_name="user_product_views")
    op.drop_index("idx_upv_product_store", table_name="user_product_views")
    op.drop_index("idx_upv_session_store", table_name="user_product_views")
    op.drop_index("idx_upv_user_store",    table_name="user_product_views")
    op.drop_table("user_product_views")
