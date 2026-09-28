"""v12 institutional intelligence and ai knowledge base

Revision ID: f83a2d7e9b12
Revises: e52b1c9d4a23
Create Date: 2026-09-28 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'f83a2d7e9b12'
down_revision = 'e52b1c9d4a23'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'knowledge_documents' not in existing_tables:
        op.create_table(
            'knowledge_documents',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title_bn', sa.String(length=500), nullable=False),
            sa.Column('title_en', sa.String(length=500), nullable=True),
            sa.Column('category', sa.String(length=80), nullable=False, server_default='MEMBERSHIP_GUIDELINES'),
            sa.Column('version', sa.String(length=40), nullable=False, server_default='2026.1'),
            sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('supersedes_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True),
            sa.Column('superseded_by_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True),
            sa.Column('publication_date', sa.DateTime(), nullable=False),
            sa.Column('effective_date', sa.DateTime(), nullable=True),
            sa.Column('author', sa.String(length=200), nullable=True),
            sa.Column('approval_status', sa.String(length=30), nullable=False, server_default='PUBLISHED'),
            sa.Column('source_type', sa.String(length=40), nullable=False, server_default='PDF'),
            sa.Column('source_url', sa.String(length=1000), nullable=True),
            sa.Column('source_entity_id', sa.Integer(), nullable=True),
            sa.Column('access_level', sa.String(length=40), nullable=False, server_default='PUBLIC'),
            sa.Column('circle_id', sa.Integer(), sa.ForeignKey('circles.id', ondelete='SET NULL'), nullable=True),
            sa.Column('raw_text', sa.Text(), nullable=True),
            sa.Column('cleaned_text', sa.Text(), nullable=True),
            sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_knowledge_documents_category', 'knowledge_documents', ['category'], unique=False)
        op.create_index('ix_knowledge_documents_is_current', 'knowledge_documents', ['is_current'], unique=False)
        op.create_index('ix_knowledge_documents_access_level', 'knowledge_documents', ['access_level'], unique=False)

    if 'knowledge_chunks' not in existing_tables:
        op.create_table(
            'knowledge_chunks',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('document_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('section_title', sa.String(length=300), nullable=True),
            sa.Column('page_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('tokens_json', sa.Text(), nullable=True),
            sa.Column('embedding_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_knowledge_chunks_document_id', 'knowledge_chunks', ['document_id'], unique=False)

    if 'knowledge_faqs' not in existing_tables:
        op.create_table(
            'knowledge_faqs',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('document_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True),
            sa.Column('question_bn', sa.String(length=500), nullable=False),
            sa.Column('question_en', sa.String(length=500), nullable=True),
            sa.Column('answer_bn', sa.Text(), nullable=False),
            sa.Column('answer_en', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=80), nullable=False, server_default='MEMBERSHIP_GUIDELINES'),
            sa.Column('section_ref', sa.String(length=200), nullable=True),
            sa.Column('page_ref', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
            sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_knowledge_faqs_status', 'knowledge_faqs', ['status'], unique=False)

    if 'ai_query_logs' not in existing_tables:
        op.create_table(
            'ai_query_logs',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('user_role', sa.String(length=60), nullable=False, server_default='PUBLIC'),
            sa.Column('assistant_mode', sa.String(length=30), nullable=False, server_default='PUBLIC'),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('question_category', sa.String(length=80), nullable=False, server_default='GENERAL'),
            sa.Column('answer_preview', sa.String(length=500), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('unanswered', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('security_flagged', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('documents_searched', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('sources_cited', sa.Text(), nullable=True),
            sa.Column('tools_called', sa.Text(), nullable=True),
            sa.Column('response_time_ms', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_query_logs_created_at', 'ai_query_logs', ['created_at'], unique=False)


def downgrade():
    pass
