"""v13 rc1 roles and membership applications tables

Revision ID: a94b3e8f1c25
Revises: f83a2d7e9b12
Create Date: 2026-09-29 05:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'a94b3e8f1c25'
down_revision = 'f83a2d7e9b12'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'roles' not in existing_tables:
        op.create_table(
            'roles',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=60), nullable=False),
            sa.Column('name_bn', sa.String(length=120), nullable=False),
            sa.Column('name_en', sa.String(length=120), nullable=False),
            sa.Column('permissions_json', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_roles_code', 'roles', ['code'], unique=True)
        op.create_index('ix_roles_is_active', 'roles', ['is_active'], unique=False)

    if 'membership_applications' not in existing_tables:
        op.create_table(
            'membership_applications',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
            sa.Column('application_no', sa.String(length=60), nullable=False),
            sa.Column('membership_type', sa.String(length=50), nullable=False, server_default='GENERAL'),
            sa.Column('circle_id', sa.Integer(), sa.ForeignKey('circles.id', ondelete='SET NULL'), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
            sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('review_note', sa.Text(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_membership_applications_member_id', 'membership_applications', ['member_id'], unique=False)
        op.create_index('ix_membership_applications_application_no', 'membership_applications', ['application_no'], unique=True)
        op.create_index('ix_membership_applications_status', 'membership_applications', ['status'], unique=False)
        op.create_index('ix_applications_status', 'membership_applications', ['status'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'membership_applications' in existing_tables:
        op.drop_table('membership_applications')
    if 'roles' in existing_tables:
        op.drop_table('roles')
