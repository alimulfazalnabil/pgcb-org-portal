"""v0.8 notices, documents, and membership application tracking"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'a8d4f1e2c901'
down_revision = 'f91a2c7d4e10'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add columns to members table
    with op.batch_alter_table('members') as batch_op:
        batch_op.add_column(sa.Column('membership_type', sa.String(length=50), nullable=False, server_default='GENERAL'))
        batch_op.add_column(sa.Column('application_no', sa.String(length=60), nullable=True))
        batch_op.create_index('ix_members_membership_type', ['membership_type'])
        batch_op.create_index('ix_members_application_no', ['application_no'], unique=True)

    # 2. Create notices table
    op.create_table(
        'notices',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('title_bn', sa.String(length=500), nullable=False),
        sa.Column('title_en', sa.String(length=500), nullable=True),
        sa.Column('content_bn', sa.Text(), nullable=False),
        sa.Column('content_en', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('category', sa.String(length=60), nullable=False, server_default='GENERAL'),
        sa.Column('attachment_url', sa.String(length=1000), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('published_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    )
    op.create_index('ix_notices_title_bn', 'notices', ['title_bn'])
    op.create_index('ix_notices_priority', 'notices', ['priority'])
    op.create_index('ix_notices_category', 'notices', ['category'])
    op.create_index('ix_notices_is_pinned', 'notices', ['is_pinned'])
    op.create_index('ix_notices_is_published', 'notices', ['is_published'])
    op.create_index('ix_notices_published_at', 'notices', ['published_at'])
    op.create_index('ix_notices_expires_at', 'notices', ['expires_at'])

    # 3. Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('title_bn', sa.String(length=500), nullable=False),
        sa.Column('title_en', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=60), nullable=False, server_default='POLICIES'),
        sa.Column('description_bn', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_type', sa.String(length=120), nullable=True),
        sa.Column('version', sa.String(length=30), nullable=False, server_default='1.0'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    )
    op.create_index('ix_documents_title_bn', 'documents', ['title_bn'])
    op.create_index('ix_documents_category', 'documents', ['category'])
    op.create_index('ix_documents_is_published', 'documents', ['is_published'])


def downgrade():
    op.drop_table('documents')
    op.drop_table('notices')
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_index('ix_members_application_no')
        batch_op.drop_index('ix_members_membership_type')
        batch_op.drop_column('application_no')
        batch_op.drop_column('membership_type')
