"""v04 admin MFA fields

Revision ID: ab42d1ef6c70
Revises: 7e3d5d4c1f20
Create Date: 2026-09-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'ab42d1ef6c70'
down_revision = '7e3d5d4c1f20'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=64), nullable=True))
    op.create_index('ix_users_mfa_enabled', 'users', ['mfa_enabled'], unique=False)


def downgrade():
    op.drop_index('ix_users_mfa_enabled', table_name='users')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
