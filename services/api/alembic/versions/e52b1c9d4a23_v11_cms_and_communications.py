"""v1.1 sprint 4 cms, news, revisions, announcements, seo metadata, and inquiry tickets"""
from alembic import op
import sqlalchemy as sa

revision = 'e52b1c9d4a23'
down_revision = 'd41f9a8b3c12'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'news_articles' not in existing_tables:
        op.create_table(
            'news_articles',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('slug', sa.String(length=240), nullable=False),
            sa.Column('title_bn', sa.String(length=500), nullable=False),
            sa.Column('title_en', sa.String(length=500), nullable=True),
            sa.Column('summary_bn', sa.Text(), nullable=True),
            sa.Column('summary_en', sa.Text(), nullable=True),
            sa.Column('content_bn', sa.Text(), nullable=False),
            sa.Column('content_en', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=80), nullable=False, server_default='GENERAL'),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('cover_image_url', sa.String(length=1000), nullable=True),
            sa.Column('gallery_urls', sa.JSON(), nullable=True),
            sa.Column('author_name', sa.String(length=200), nullable=True),
            sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
            sa.Column('scheduled_at', sa.DateTime(), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('seo_title', sa.String(length=300), nullable=True),
            sa.Column('meta_description', sa.Text(), nullable=True),
            sa.Column('canonical_url', sa.String(length=500), nullable=True),
            sa.Column('og_image_url', sa.String(length=1000), nullable=True),
            sa.Column('robots', sa.String(length=60), nullable=False, server_default='index,follow'),
            sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_news_articles_slug', 'news_articles', ['slug'], unique=True)
        op.create_index('ix_news_articles_title_bn', 'news_articles', ['title_bn'], unique=False)
        op.create_index('ix_news_articles_category', 'news_articles', ['category'], unique=False)
        op.create_index('ix_news_articles_status', 'news_articles', ['status'], unique=False)
        op.create_index('ix_news_articles_is_published', 'news_articles', ['is_published'], unique=False)

    if 'content_revisions' not in existing_tables:
        op.create_table(
            'content_revisions',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('workflow_status', sa.String(length=30), nullable=False, server_default='DRAFT'),
            sa.Column('snapshot', sa.JSON(), nullable=True),
            sa.Column('change_summary', sa.String(length=500), nullable=True),
            sa.Column('changed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('published_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_content_revisions_entity', 'content_revisions', ['entity_type', 'entity_id'], unique=False)

    if 'announcements' not in existing_tables:
        op.create_table(
            'announcements',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title_bn', sa.String(length=500), nullable=False),
            sa.Column('title_en', sa.String(length=500), nullable=True),
            sa.Column('body_bn', sa.Text(), nullable=False),
            sa.Column('body_en', sa.Text(), nullable=True),
            sa.Column('target_scope', sa.String(length=40), nullable=False, server_default='ALL_MEMBERS'),
            sa.Column('target_circle_id', sa.Integer(), sa.ForeignKey('circles.id', ondelete='SET NULL'), nullable=True),
            sa.Column('target_status', sa.String(length=40), nullable=True),
            sa.Column('channels', sa.JSON(), nullable=True),
            sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('sent_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('published_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_announcements_target_scope', 'announcements', ['target_scope'], unique=False)

    if 'seo_metadata' not in existing_tables:
        op.create_table(
            'seo_metadata',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('slug', sa.String(length=240), nullable=True),
            sa.Column('seo_title', sa.String(length=300), nullable=True),
            sa.Column('meta_description', sa.Text(), nullable=True),
            sa.Column('canonical_url', sa.String(length=500), nullable=True),
            sa.Column('og_image_url', sa.String(length=1000), nullable=True),
            sa.Column('robots', sa.String(length=60), nullable=False, server_default='index,follow'),
            sa.Column('structured_data', sa.JSON(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('entity_type', 'entity_id', name='uq_seo_metadata_entity'),
        )
        op.create_index('ix_seo_metadata_entity', 'seo_metadata', ['entity_type', 'entity_id'], unique=False)

    if 'contact_inquiry_meta' not in existing_tables:
        op.create_table(
            'contact_inquiry_meta',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('message_id', sa.Integer(), sa.ForeignKey('contact_messages.id', ondelete='CASCADE'), nullable=False),
            sa.Column('ticket_no', sa.String(length=60), nullable=False),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='NEW'),
            sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('response_text', sa.Text(), nullable=True),
            sa.Column('responded_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('responded_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_contact_inquiry_meta_message_id', 'contact_inquiry_meta', ['message_id'], unique=True)
        op.create_index('ix_contact_inquiry_meta_ticket_no', 'contact_inquiry_meta', ['ticket_no'], unique=True)


def downgrade():
    pass
