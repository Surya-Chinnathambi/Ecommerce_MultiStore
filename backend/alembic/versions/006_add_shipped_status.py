"""006_add_shipped_status — add 'shipped' to orderstatus enum, add user_id index on orders

The UI and admin panel use 'shipped' as an order status but the original
orderstatus PostgreSQL enum only contained 'ready'.  This migration adds
'shipped' to the enum and backfills any existing 'ready' orders to 'shipped'
so everything stays consistent.

It also adds a user_id index to the orders table to speed up the
/orders/customer endpoint that now queries by user_id OR customer_email.

Revision ID: 006_add_shipped_status
Revises: 005_advanced_features
"""
from alembic import op
import sqlalchemy as sa

revision = "006_add_shipped_status"
down_revision = "005_advanced_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Add 'shipped' to the orderstatus enum ──────────────────────────────
    # PostgreSQL requires ALTER TYPE … ADD VALUE which cannot run inside a
    # transaction block, so we execute it with autocommit.
    connection = op.get_bind()

    # Only add if not already present (idempotent)
    result = connection.execute(
        sa.text(
            "SELECT 1 FROM pg_enum "
            "JOIN pg_type ON pg_type.oid = pg_enum.enumtypid "
            "WHERE pg_type.typname = 'orderstatus' "
            "AND pg_enum.enumlabel = 'shipped'"
        )
    ).fetchone()

    if result is None:
        # Commit current transaction so ALTER TYPE can run outside it
        connection.execute(sa.text("COMMIT"))
        connection.execute(
            sa.text("ALTER TYPE orderstatus ADD VALUE 'shipped' AFTER 'processing'")
        )
        # Begin a new transaction for the rest of this migration
        connection.execute(sa.text("BEGIN"))

    # ── 2. Back-fill 'ready' → 'shipped' ─────────────────────────────────────
    # 'ready' was the original name for what the UI calls 'shipped'.
    # Cast through text to satisfy the enum constraint transition.
    connection.execute(
        sa.text(
            "UPDATE orders SET order_status = 'shipped'::orderstatus "
            "WHERE order_status = 'ready'::orderstatus"
        )
    )

    # ── 3. Add index on orders.user_id ────────────────────────────────────────
    op.create_index(
        "idx_order_user_id",
        "orders",
        ["user_id"],
    )


def downgrade() -> None:
    # Remove the index
    op.drop_index("idx_order_user_id", table_name="orders")

    # Revert 'shipped' back to 'ready'
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE orders SET order_status = 'ready'::orderstatus "
            "WHERE order_status = 'shipped'::orderstatus"
        )
    )

    # Note: PostgreSQL does not support removing enum values.
    # The 'shipped' label will remain in the type after downgrade.
