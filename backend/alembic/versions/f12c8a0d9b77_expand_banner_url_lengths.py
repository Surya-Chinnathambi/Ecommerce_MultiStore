"""expand banner URL lengths

Revision ID: f12c8a0d9b77
Revises: c7d3e9f1a2b4
Create Date: 2026-03-10 16:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f12c8a0d9b77"
down_revision: Union[str, None] = "c7d3e9f1a2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "promotional_banners",
        "image_url",
        existing_type=sa.String(length=500),
        type_=sa.String(length=2048),
        existing_nullable=True,
    )
    op.alter_column(
        "promotional_banners",
        "link_url",
        existing_type=sa.String(length=500),
        type_=sa.String(length=2048),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "promotional_banners",
        "link_url",
        existing_type=sa.String(length=2048),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        "promotional_banners",
        "image_url",
        existing_type=sa.String(length=2048),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
