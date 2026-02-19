"""security_hardening

Revision ID: 003_security
Revises: 002_marketplace
Create Date: 2026-02-19

Adds:
  - api_keys table (B2B / POS / sync-agent authentication)
  - Indexes on api_keys.key_hash, store_id, user_id
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_security'
down_revision = '002_marketplace'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── api_keys ─────────────────────────────────────────────────────────────
    op.create_table(
        'api_keys',
        sa.Column('id',             postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name',           sa.String(100),  nullable=False),
        sa.Column('key_hash',       sa.String(64),   nullable=False),
        sa.Column('key_prefix',     sa.String(16),   nullable=False),
        sa.Column('is_test',        sa.Boolean(),    nullable=False, server_default='false'),

        # Ownership
        sa.Column('store_id',       postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id',    ondelete='CASCADE'), nullable=True),
        sa.Column('user_id',        postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id',     ondelete='SET NULL'), nullable=True),

        # Scopes stored as Postgres text array
        sa.Column('scopes',         postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),

        # Lifecycle
        sa.Column('is_active',      sa.Boolean(),    nullable=False, server_default='true'),
        sa.Column('expires_at',     sa.DateTime(),   nullable=True),
        sa.Column('last_used_at',   sa.DateTime(),   nullable=True),
        sa.Column('request_count',  sa.Integer(),    nullable=False, server_default='0'),
        sa.Column('revoked_at',     sa.DateTime(),   nullable=True),

        # Timestamps
        sa.Column('created_at',     sa.DateTime(),   nullable=False, server_default=sa.text('NOW()')),
    )

    # Unique constraint + indexes
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_store_id', 'api_keys', ['store_id'])
    op.create_index('ix_api_keys_user_id',  'api_keys', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_api_keys_user_id',  table_name='api_keys')
    op.drop_index('ix_api_keys_store_id', table_name='api_keys')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    op.drop_table('api_keys')
