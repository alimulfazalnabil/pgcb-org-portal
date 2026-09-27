"""v0.9 member search and directory performance indexes"""
from alembic import op
import sqlalchemy as sa

revision = 'c2048b9f1d09'
down_revision = 'a8d4f1e2c901'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_users_name_bn', 'users', ['name_bn'], unique=False)
    op.create_index('ix_members_employee_id', 'members', ['employee_id'], unique=False)
    op.create_index('ix_members_created_at', 'members', ['created_at'], unique=False)
    op.create_index('ix_members_status_circle_id', 'members', ['status', 'circle_id'], unique=False)


def downgrade():
    op.drop_index('ix_members_status_circle_id', table_name='members')
    op.drop_index('ix_members_created_at', table_name='members')
    op.drop_index('ix_members_employee_id', table_name='members')
    op.drop_index('ix_users_name_bn', table_name='users')
