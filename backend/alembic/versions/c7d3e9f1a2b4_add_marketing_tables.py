"""add marketing tables

Revision ID: c7d3e9f1a2b4
Revises: b4a24dae6993
Create Date: 2026-03-10 09:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c7d3e9f1a2b4"
down_revision: Union[str, None] = "b4a24dae6993"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BANNER_TYPE_ENUM = postgresql.ENUM(
    "hero",
    "promotional",
    "category",
    "flash_sale",
    name="bannertype",
    create_type=False,
)

BANNER_STATUS_ENUM = postgresql.ENUM(
    "active",
    "inactive",
    "scheduled",
    name="bannerstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    BANNER_TYPE_ENUM.create(bind, checkfirst=True)
    BANNER_STATUS_ENUM.create(bind, checkfirst=True)

    if not inspector.has_table("promotional_banners"):
        op.create_table(
            "promotional_banners",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("subtitle", sa.String(length=500), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("link_url", sa.String(length=500), nullable=True),
            sa.Column("banner_type", BANNER_TYPE_ENUM, nullable=True, server_default="promotional"),
            sa.Column("status", BANNER_STATUS_ENUM, nullable=True, server_default="active"),
            sa.Column("start_date", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
            sa.Column("end_date", sa.DateTime(), nullable=True),
            sa.Column("display_order", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("click_count", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        )
        op.create_index("ix_promotional_banners_store_id", "promotional_banners", ["store_id"], unique=False)

    if not inspector.has_table("flash_sales"):
        op.create_table(
            "flash_sales",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("original_price", sa.Float(), nullable=False),
            sa.Column("sale_price", sa.Float(), nullable=False),
            sa.Column("discount_percent", sa.Float(), nullable=True),
            sa.Column("start_time", sa.DateTime(), nullable=False),
            sa.Column("end_time", sa.DateTime(), nullable=False),
            sa.Column("max_quantity", sa.Integer(), nullable=True),
            sa.Column("sold_quantity", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        )
        op.create_index("ix_flash_sales_store_id", "flash_sales", ["store_id"], unique=False)
        op.create_index("ix_flash_sales_product_id", "flash_sales", ["product_id"], unique=False)

    if not inspector.has_table("social_proof_activities"):
        op.create_table(
            "social_proof_activities",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
            sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
            sa.Column("user_name", sa.String(length=100), nullable=True),
            sa.Column("city", sa.String(length=100), nullable=True),
            sa.Column("activity_type", sa.String(length=50), nullable=True),
            sa.Column("message", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        )
        op.create_index("ix_social_proof_activities_store_id", "social_proof_activities", ["store_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("social_proof_activities"):
        op.drop_index("ix_social_proof_activities_store_id", table_name="social_proof_activities")
        op.drop_table("social_proof_activities")

    if inspector.has_table("flash_sales"):
        op.drop_index("ix_flash_sales_product_id", table_name="flash_sales")
        op.drop_index("ix_flash_sales_store_id", table_name="flash_sales")
        op.drop_table("flash_sales")

    if inspector.has_table("promotional_banners"):
        op.drop_index("ix_promotional_banners_store_id", table_name="promotional_banners")
        op.drop_table("promotional_banners")

    BANNER_STATUS_ENUM.drop(bind, checkfirst=True)
    BANNER_TYPE_ENUM.drop(bind, checkfirst=True)
