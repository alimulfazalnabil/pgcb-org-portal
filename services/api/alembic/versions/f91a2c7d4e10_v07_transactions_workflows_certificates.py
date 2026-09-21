"""v0.7 transaction engine, notification retries, lifecycle, certificates, CMS workflows"""
from alembic import op
import sqlalchemy as sa

revision = 'f91a2c7d4e10'
down_revision = 'ef6c3a8a2e10'
branch_labels = None
depends_on = None


def _index(name, table, cols, unique=False):
    op.create_index(name, table, cols, unique=unique)


def upgrade():
    # Asynchronous notification delivery metadata.
    op.add_column('notification_deliveries', sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('notification_deliveries', sa.Column('next_attempt_at', sa.DateTime(), nullable=True))
    op.add_column('notification_deliveries', sa.Column('last_attempt_at', sa.DateTime(), nullable=True))
    op.add_column('notification_deliveries', sa.Column('idempotency_key', sa.String(length=180), nullable=True))
    _index('ix_notification_deliveries_next_attempt_at', 'notification_deliveries', ['next_attempt_at'])
    _index('ix_notification_deliveries_idempotency_key', 'notification_deliveries', ['idempotency_key'], unique=True)

    op.create_table(
        'payment_webhook_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.String(length=40), nullable=False),
        sa.Column('event_id', sa.String(length=160), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('signature_valid', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('processing_status', sa.String(length=30), nullable=False, server_default='RECEIVED'),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('payment_transactions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('event_id', name='uq_payment_webhook_event_id'),
    )
    for name, col in [
        ('ix_payment_webhook_events_provider', 'provider'),
        ('ix_payment_webhook_events_event_id', 'event_id'),
        ('ix_payment_webhook_events_event_type', 'event_type'),
        ('ix_payment_webhook_events_signature_valid', 'signature_valid'),
        ('ix_payment_webhook_events_processing_status', 'processing_status'),
        ('ix_payment_webhook_events_payment_id', 'payment_id'),
        ('ix_payment_webhook_events_created_at', 'created_at'),
    ]:
        _index(name, 'payment_webhook_events', [col], unique=(col == 'event_id'))

    op.create_table(
        'membership_renewals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('payment_transactions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('previous_validity_date', sa.DateTime(), nullable=True),
        sa.Column('new_validity_date', sa.DateTime(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='BDT'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    for name, col in [('ix_membership_renewals_member_id', 'member_id'), ('ix_membership_renewals_payment_id', 'payment_id'), ('ix_membership_renewals_status', 'status'), ('ix_membership_renewals_created_at', 'created_at')]:
        _index(name, 'membership_renewals', [col])

    op.create_table(
        'membership_reminders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('validity_date', sa.DateTime(), nullable=False),
        sa.Column('reminder_type', sa.String(length=30), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('member_id', 'validity_date', 'reminder_type', name='uq_membership_reminder'),
    )
    for name, col in [('ix_membership_reminders_member_id', 'member_id'), ('ix_membership_reminders_validity_date', 'validity_date'), ('ix_membership_reminders_reminder_type', 'reminder_type'), ('ix_membership_reminders_created_at', 'created_at')]:
        _index(name, 'membership_reminders', [col])

    op.create_table(
        'certificates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('certificate_no', sa.String(length=120), nullable=False),
        sa.Column('recipient_name', sa.String(length=250), nullable=False),
        sa.Column('title_bn', sa.String(length=500), nullable=False),
        sa.Column('issue_date', sa.DateTime(), nullable=False),
        sa.Column('event_registration_id', sa.Integer(), sa.ForeignKey('event_registrations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verification_token_hash', sa.String(length=128), nullable=False),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('pdf_path', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('certificate_no', name='uq_certificate_no'),
        sa.UniqueConstraint('verification_token_hash', name='uq_certificate_token_hash'),
    )
    for name, col, unique in [
        ('ix_certificates_certificate_no', 'certificate_no', True),
        ('ix_certificates_issue_date', 'issue_date', False),
        ('ix_certificates_event_registration_id', 'event_registration_id', False),
        ('ix_certificates_member_id', 'member_id', False),
        ('ix_certificates_verification_token_hash', 'verification_token_hash', True),
        ('ix_certificates_created_at', 'created_at', False),
    ]:
        _index(name, 'certificates', [col], unique=unique)

    op.create_table(
        'content_workflows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('review_note', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('published_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('entity_type', 'entity_id', name='uq_content_workflow_entity'),
    )
    for name, col in [('ix_content_workflows_entity_type', 'entity_type'), ('ix_content_workflows_entity_id', 'entity_id'), ('ix_content_workflows_status', 'status'), ('ix_content_workflows_scheduled_at', 'scheduled_at')]:
        _index(name, 'content_workflows', [col])


def downgrade():
    for name in ['ix_content_workflows_scheduled_at', 'ix_content_workflows_status', 'ix_content_workflows_entity_id', 'ix_content_workflows_entity_type']:
        op.drop_index(name, table_name='content_workflows')
    op.drop_table('content_workflows')

    for name in ['ix_certificates_created_at', 'ix_certificates_verification_token_hash', 'ix_certificates_member_id', 'ix_certificates_event_registration_id', 'ix_certificates_issue_date', 'ix_certificates_certificate_no']:
        op.drop_index(name, table_name='certificates')
    op.drop_table('certificates')

    for name in ['ix_membership_reminders_created_at', 'ix_membership_reminders_reminder_type', 'ix_membership_reminders_validity_date', 'ix_membership_reminders_member_id']:
        op.drop_index(name, table_name='membership_reminders')
    op.drop_table('membership_reminders')

    for name in ['ix_membership_renewals_created_at', 'ix_membership_renewals_status', 'ix_membership_renewals_payment_id', 'ix_membership_renewals_member_id']:
        op.drop_index(name, table_name='membership_renewals')
    op.drop_table('membership_renewals')

    for name in ['ix_payment_webhook_events_created_at', 'ix_payment_webhook_events_payment_id', 'ix_payment_webhook_events_processing_status', 'ix_payment_webhook_events_signature_valid', 'ix_payment_webhook_events_event_type', 'ix_payment_webhook_events_event_id', 'ix_payment_webhook_events_provider']:
        op.drop_index(name, table_name='payment_webhook_events')
    op.drop_table('payment_webhook_events')

    op.drop_index('ix_notification_deliveries_idempotency_key', table_name='notification_deliveries')
    op.drop_index('ix_notification_deliveries_next_attempt_at', table_name='notification_deliveries')
    op.drop_column('notification_deliveries', 'idempotency_key')
    op.drop_column('notification_deliveries', 'last_attempt_at')
    op.drop_column('notification_deliveries', 'next_attempt_at')
    op.drop_column('notification_deliveries', 'attempts')
