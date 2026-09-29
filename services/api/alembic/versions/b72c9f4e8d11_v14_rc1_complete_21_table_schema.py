"""v14 rc1 complete 21-table production schema

Revision ID: b72c9f4e8d11
Revises: a94b3e8f1c25
Create Date: 2026-09-29 05:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'b72c9f4e8d11'
down_revision = 'a94b3e8f1c25'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'membership_applications' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('membership_applications')}
        if 'deleted_at' not in cols:
            op.add_column('membership_applications', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    if 'permissions' not in existing_tables:
        op.create_table(
            'permissions',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=100), nullable=False),
            sa.Column('module', sa.String(length=60), nullable=False, server_default='CORE'),
            sa.Column('description_en', sa.String(length=300), nullable=True),
            sa.Column('description_bn', sa.String(length=300), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_permissions_code', 'permissions', ['code'], unique=True)
        op.create_index('ix_permissions_module', 'permissions', ['module'], unique=False)

    if 'grid_circles' not in existing_tables:
        op.create_table(
            'grid_circles',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=40), nullable=False),
            sa.Column('name_bn', sa.String(length=120), nullable=False),
            sa.Column('name_en', sa.String(length=120), nullable=False),
            sa.Column('region', sa.String(length=120), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_grid_circles_code', 'grid_circles', ['code'], unique=True)
        op.create_index('ix_grid_circles_name_bn', 'grid_circles', ['name_bn'], unique=True)

    if 'memberships' not in existing_tables:
        op.create_table(
            'memberships',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
            sa.Column('membership_id', sa.String(length=50), nullable=False),
            sa.Column('membership_type', sa.String(length=50), nullable=False, server_default='GENERAL'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
            sa.Column('issue_date', sa.DateTime(), nullable=False),
            sa.Column('validity_date', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_memberships_member_id', 'memberships', ['member_id'], unique=False)
        op.create_index('ix_memberships_membership_id', 'memberships', ['membership_id'], unique=True)
        op.create_index('ix_memberships_status', 'memberships', ['status'], unique=False)

    if 'application_reviews' not in existing_tables:
        op.create_table(
            'application_reviews',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('application_id', sa.Integer(), sa.ForeignKey('membership_applications.id', ondelete='CASCADE'), nullable=True),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
            sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('action', sa.String(length=40), nullable=False),
            sa.Column('previous_status', sa.String(length=30), nullable=True),
            sa.Column('new_status', sa.String(length=30), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_application_reviews_member_id', 'application_reviews', ['member_id'], unique=False)
        op.create_index('ix_application_reviews_action', 'application_reviews', ['action'], unique=False)

    if 'payments' not in existing_tables:
        op.create_table(
            'payments',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='SET NULL'), nullable=True),
            sa.Column('transaction_id', sa.String(length=120), nullable=False),
            sa.Column('receipt_no', sa.String(length=80), nullable=True),
            sa.Column('provider', sa.String(length=40), nullable=False, server_default='BKASH'),
            sa.Column('purpose', sa.String(length=50), nullable=False, server_default='MEMBERSHIP'),
            sa.Column('amount', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('currency', sa.String(length=10), nullable=False, server_default='BDT'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='PENDING'),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_payments_transaction_id', 'payments', ['transaction_id'], unique=True)
        op.create_index('ix_payments_receipt_no', 'payments', ['receipt_no'], unique=True)
        op.create_index('ix_payments_status', 'payments', ['status'], unique=False)

    if 'news' not in existing_tables:
        op.create_table(
            'news',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('slug', sa.String(length=240), nullable=False),
            sa.Column('title_bn', sa.String(length=500), nullable=False),
            sa.Column('title_en', sa.String(length=500), nullable=True),
            sa.Column('summary_bn', sa.Text(), nullable=True),
            sa.Column('content_bn', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=80), nullable=False, server_default='GENERAL'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='PUBLISHED'),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_news_slug', 'news', ['slug'], unique=True)
        op.create_index('ix_news_status', 'news', ['status'], unique=False)

    if 'notification_templates' not in existing_tables:
        op.create_table(
            'notification_templates',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=80), nullable=False),
            sa.Column('channel', sa.String(length=30), nullable=False, server_default='EMAIL'),
            sa.Column('subject_bn', sa.String(length=300), nullable=False),
            sa.Column('subject_en', sa.String(length=300), nullable=True),
            sa.Column('body_bn', sa.Text(), nullable=False),
            sa.Column('body_en', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_notification_templates_code', 'notification_templates', ['code'], unique=True)

    if 'ai_conversations' not in existing_tables:
        op.create_table(
            'ai_conversations',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('session_id', sa.String(length=120), nullable=False, server_default=''),
            sa.Column('title', sa.String(length=300), nullable=True),
            sa.Column('mode', sa.String(length=30), nullable=False, server_default='PUBLIC'),
            sa.Column('language', sa.String(length=10), nullable=False, server_default='bn'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'], unique=False)
        op.create_index('ix_ai_conversations_session_id', 'ai_conversations', ['session_id'], unique=False)

    if 'ai_messages' not in existing_tables:
        op.create_table(
            'ai_messages',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('content_bn', sa.Text(), nullable=True),
            sa.Column('content_en', sa.Text(), nullable=True),
            sa.Column('intent', sa.String(length=80), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=True),
            sa.Column('confidence_state', sa.String(length=20), nullable=True),
            sa.Column('sources', sa.Text(), nullable=True),
            sa.Column('tools_used', sa.Text(), nullable=True),
            sa.Column('actions', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for tbl in (
        'ai_messages',
        'ai_conversations',
        'notification_templates',
        'news',
        'payments',
        'application_reviews',
        'memberships',
        'grid_circles',
        'permissions',
    ):
        if tbl in existing_tables:
            op.drop_table(tbl)
