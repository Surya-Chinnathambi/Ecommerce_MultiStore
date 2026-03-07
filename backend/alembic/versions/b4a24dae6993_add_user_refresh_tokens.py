"""add_user_refresh_tokens

Revision ID: b4a24dae6993
Revises: 006_add_shipped_status
Create Date: 2026-03-08 02:19:32.993431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4a24dae6993'
down_revision: Union[str, None] = '006_add_shipped_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('jti', sa.String(length=255), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_refresh_tokens_jti'), 'user_refresh_tokens', ['jti'], unique=True)
    op.create_index(op.f('ix_user_refresh_tokens_user_id'), 'user_refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_refresh_tokens_user_id'), table_name='user_refresh_tokens')
    op.drop_index(op.f('ix_user_refresh_tokens_jti'), table_name='user_refresh_tokens')
    op.drop_table('user_refresh_tokens')
