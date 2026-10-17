"""v15_phase6_events_notifications_phase7_support_tickets

Revision ID: e8f4a1b9c321
Revises: b72c9f4e8d11
Create Date: 2026-10-17 04:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'e8f4a1b9c321'
down_revision = 'b72c9f4e8d11'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # -------------------------------------------------------------------------
    # 1. Column Additions to Pre-existing Tables
    # -------------------------------------------------------------------------

    # 1.1 events table
    if 'events' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('events')}
        with op.batch_alter_table('events') as batch_op:
            if 'category' not in cols:
                batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=False, server_default='SEMINAR'))
            if 'status' not in cols:
                batch_op.add_column(sa.Column('status', sa.String(length=30), nullable=False, server_default='PUBLISHED'))
            if 'description_en' not in cols:
                batch_op.add_column(sa.Column('description_en', sa.Text(), nullable=True))
            if 'start_date' not in cols:
                batch_op.add_column(sa.Column('start_date', sa.DateTime(), nullable=True))
            if 'end_date' not in cols:
                batch_op.add_column(sa.Column('end_date', sa.DateTime(), nullable=True))
            if 'start_time' not in cols:
                batch_op.add_column(sa.Column('start_time', sa.String(length=30), nullable=True))
            if 'end_time' not in cols:
                batch_op.add_column(sa.Column('end_time', sa.String(length=30), nullable=True))
            if 'venue' not in cols:
                batch_op.add_column(sa.Column('venue', sa.String(length=300), nullable=True))
            if 'location_en' not in cols:
                batch_op.add_column(sa.Column('location_en', sa.String(length=300), nullable=True))
            if 'is_online' not in cols:
                batch_op.add_column(sa.Column('is_online', sa.Boolean(), nullable=False, server_default=sa.text('false')))
            if 'meeting_link' not in cols:
                batch_op.add_column(sa.Column('meeting_link', sa.String(length=1000), nullable=True))
            if 'certificate_eligible' not in cols:
                batch_op.add_column(sa.Column('certificate_eligible', sa.Boolean(), nullable=False, server_default=sa.text('false')))
            if 'eligibility_criteria' not in cols:
                batch_op.add_column(sa.Column('eligibility_criteria', sa.String(length=50), nullable=False, server_default='ALL_MEMBERS'))
            if 'updated_at' not in cols:
                batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))

    # 1.2 event_registrations table
    if 'event_registrations' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('event_registrations')}
        with op.batch_alter_table('event_registrations') as batch_op:
            if 'member_id' not in cols:
                batch_op.add_column(sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', name='fk_event_registrations_member_id', ondelete='SET NULL'), nullable=True))
            if 'waitlist_position' not in cols:
                batch_op.add_column(sa.Column('waitlist_position', sa.Integer(), nullable=True))
            if 'qr_token' not in cols:
                batch_op.add_column(sa.Column('qr_token', sa.String(length=128), nullable=True))
            if 'cancelled_at' not in cols:
                batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
            if 'cancellation_reason' not in cols:
                batch_op.add_column(sa.Column('cancellation_reason', sa.Text(), nullable=True))

    # 1.3 notifications table
    if 'notifications' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('notifications')}
        with op.batch_alter_table('notifications') as batch_op:
            if 'title_en' not in cols:
                batch_op.add_column(sa.Column('title_en', sa.String(length=300), nullable=True))
            if 'body_en' not in cols:
                batch_op.add_column(sa.Column('body_en', sa.Text(), nullable=True))
            if 'data_json' not in cols:
                batch_op.add_column(sa.Column('data_json', sa.JSON(), nullable=True))
            if 'priority' not in cols:
                batch_op.add_column(sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'))
            if 'expires_at' not in cols:
                batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=True))

    # 1.4 member_documents table
    if 'member_documents' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('member_documents')}
        with op.batch_alter_table('member_documents') as batch_op:
            if 'title' not in cols:
                batch_op.add_column(sa.Column('title', sa.String(length=255), nullable=True))
            if 'file_size' not in cols:
                batch_op.add_column(sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'))
            if 'version' not in cols:
                batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
            if 'reviewer_note' not in cols:
                batch_op.add_column(sa.Column('reviewer_note', sa.Text(), nullable=True))
            if 'verified_at' not in cols:
                batch_op.add_column(sa.Column('verified_at', sa.DateTime(), nullable=True))
            if 'expires_at' not in cols:
                batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=True))
            if 'deleted_at' not in cols:
                batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # 1.5 certificates table
    if 'certificates' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('certificates')}
        with op.batch_alter_table('certificates') as batch_op:
            if 'title_en' not in cols:
                batch_op.add_column(sa.Column('title_en', sa.String(length=500), nullable=True))
            if 'certificate_type' not in cols:
                batch_op.add_column(sa.Column('certificate_type', sa.String(length=50), nullable=False, server_default='MEMBERSHIP'))
            if 'status' not in cols:
                batch_op.add_column(sa.Column('status', sa.String(length=30), nullable=False, server_default='VALID'))
            if 'revoked_at' not in cols:
                batch_op.add_column(sa.Column('revoked_at', sa.DateTime(), nullable=True))
            if 'revoked_by_id' not in cols:
                batch_op.add_column(sa.Column('revoked_by_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_certificates_revoked_by_id', ondelete='SET NULL'), nullable=True))
            if 'revocation_reason' not in cols:
                batch_op.add_column(sa.Column('revocation_reason', sa.Text(), nullable=True))

    # 1.6 membership_renewals table
    if 'membership_renewals' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('membership_renewals')}
        with op.batch_alter_table('membership_renewals') as batch_op:
            if 'duration_years' not in cols:
                batch_op.add_column(sa.Column('duration_years', sa.Integer(), nullable=False, server_default='1'))
            if 'notes' not in cols:
                batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))

    # 1.7 member_profile_change_requests table
    if 'member_profile_change_requests' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('member_profile_change_requests')}
        with op.batch_alter_table('member_profile_change_requests') as batch_op:
            if 'supporting_document_id' not in cols:
                batch_op.add_column(sa.Column('supporting_document_id', sa.Integer(), sa.ForeignKey('member_documents.id', name='fk_mpcr_supporting_document_id', ondelete='SET NULL'), nullable=True))

    # -------------------------------------------------------------------------
    # 2. Creation of 8 Missing Tables in Dependency Order
    # -------------------------------------------------------------------------

    # 2.1 document_versions (depends on member_documents)
    if 'document_versions' not in existing_tables:
        op.create_table(
            'document_versions',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('document_id', sa.Integer(), sa.ForeignKey('member_documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('storage_path', sa.String(length=1000), nullable=False),
            sa.Column('content_type', sa.String(length=120), nullable=True),
            sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('review_status', sa.String(length=30), nullable=False, server_default='UNDER_REVIEW'),
            sa.Column('reviewer_note', sa.Text(), nullable=True),
            sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'], unique=False)

    # 2.2 document_verification_events (depends on member_documents, users)
    if 'document_verification_events' not in existing_tables:
        op.create_table(
            'document_verification_events',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('document_id', sa.Integer(), sa.ForeignKey('member_documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('action', sa.String(length=40), nullable=False),
            sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('previous_status', sa.String(length=30), nullable=True),
            sa.Column('new_status', sa.String(length=30), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_document_verification_events_document_id', 'document_verification_events', ['document_id'], unique=False)
        op.create_index('ix_document_verification_events_action', 'document_verification_events', ['action'], unique=False)
        op.create_index('ix_document_verification_events_new_status', 'document_verification_events', ['new_status'], unique=False)
        op.create_index('ix_document_verification_events_created_at', 'document_verification_events', ['created_at'], unique=False)

    # 2.3 digital_member_ids (depends on members)
    if 'digital_member_ids' not in existing_tables:
        op.create_table(
            'digital_member_ids',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
            sa.Column('identifier', sa.String(length=80), nullable=False),
            sa.Column('qr_token', sa.String(length=128), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('issued_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('valid_from', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('revocation_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_digital_member_ids_member_id', 'digital_member_ids', ['member_id'], unique=False)
        op.create_index('ix_digital_member_ids_identifier', 'digital_member_ids', ['identifier'], unique=True)
        op.create_index('ix_digital_member_ids_qr_token', 'digital_member_ids', ['qr_token'], unique=True)
        op.create_index('ix_digital_member_ids_status', 'digital_member_ids', ['status'], unique=False)

    # 2.4 certificate_verification_records (depends on certificates, users)
    if 'certificate_verification_records' not in existing_tables:
        op.create_table(
            'certificate_verification_records',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('certificate_id', sa.Integer(), sa.ForeignKey('certificates.id', ondelete='CASCADE'), nullable=False),
            sa.Column('action', sa.String(length=40), nullable=False),
            sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_certificate_verification_records_certificate_id', 'certificate_verification_records', ['certificate_id'], unique=False)
        op.create_index('ix_certificate_verification_records_action', 'certificate_verification_records', ['action'], unique=False)
        op.create_index('ix_certificate_verification_records_created_at', 'certificate_verification_records', ['created_at'], unique=False)

    # 2.5 event_attendance (depends on events, event_registrations, members, users)
    if 'event_attendance' not in existing_tables:
        op.create_table(
            'event_attendance',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False),
            sa.Column('registration_id', sa.Integer(), sa.ForeignKey('event_registrations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='SET NULL'), nullable=True),
            sa.Column('checked_in_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('checked_out_at', sa.DateTime(), nullable=True),
            sa.Column('checked_in_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('method', sa.String(length=30), nullable=False, server_default='QR'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('event_id', 'member_id', name='uq_event_attendance_member'),
        )
        op.create_index('ix_event_attendance_event_id', 'event_attendance', ['event_id'], unique=False)
        op.create_index('ix_event_attendance_registration_id', 'event_attendance', ['registration_id'], unique=False)
        op.create_index('ix_event_attendance_member_id', 'event_attendance', ['member_id'], unique=False)
        op.create_index('ix_event_attendance_checked_in_at', 'event_attendance', ['checked_in_at'], unique=False)

    # 2.6 membership_status_history (depends on members, users, payment_transactions, certificates)
    if 'membership_status_history' not in existing_tables:
        op.create_table(
            'membership_status_history',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='CASCADE'), nullable=False),
            sa.Column('old_status', sa.String(length=30), nullable=True),
            sa.Column('new_status', sa.String(length=30), nullable=False),
            sa.Column('old_validity', sa.DateTime(), nullable=True),
            sa.Column('new_validity', sa.DateTime(), nullable=True),
            sa.Column('action', sa.String(length=60), nullable=False, server_default='STATUS_CHANGE'),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('performed_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('payment_id', sa.Integer(), sa.ForeignKey('payment_transactions.id', ondelete='SET NULL'), nullable=True),
            sa.Column('certificate_id', sa.Integer(), sa.ForeignKey('certificates.id', ondelete='SET NULL'), nullable=True),
            sa.Column('effective_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_membership_status_history_member_id', 'membership_status_history', ['member_id'], unique=False)
        op.create_index('ix_membership_status_history_new_status', 'membership_status_history', ['new_status'], unique=False)
        op.create_index('ix_membership_status_history_action', 'membership_status_history', ['action'], unique=False)
        op.create_index('ix_membership_status_history_effective_at', 'membership_status_history', ['effective_at'], unique=False)
        op.create_index('ix_membership_status_history_created_at', 'membership_status_history', ['created_at'], unique=False)

    # 2.7 notification_preferences (depends on users)
    if 'notification_preferences' not in existing_tables:
        op.create_table(
            'notification_preferences',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('in_app', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('email', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('sms', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('user_id', 'category', name='uq_user_notification_preference'),
        )
        op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'], unique=False)
        op.create_index('ix_notification_preferences_category', 'notification_preferences', ['category'], unique=False)

    # 2.8 support_tickets (depends on users, members, ai_conversations)
    if 'support_tickets' not in existing_tables:
        op.create_table(
            'support_tickets',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ticket_no', sa.String(length=60), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='SET NULL'), nullable=True),
            sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('ai_conversations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('subject', sa.String(length=300), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=80), nullable=False, server_default='GENERAL'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),
            sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
            sa.Column('assigned_to', sa.String(length=200), nullable=True),
            sa.Column('resolution_note', sa.Text(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_support_tickets_ticket_no', 'support_tickets', ['ticket_no'], unique=True)
        op.create_index('ix_support_tickets_user_id', 'support_tickets', ['user_id'], unique=False)
        op.create_index('ix_support_tickets_member_id', 'support_tickets', ['member_id'], unique=False)
        op.create_index('ix_support_tickets_conversation_id', 'support_tickets', ['conversation_id'], unique=False)
        op.create_index('ix_support_tickets_category', 'support_tickets', ['category'], unique=False)
        op.create_index('ix_support_tickets_status', 'support_tickets', ['status'], unique=False)
        op.create_index('ix_support_tickets_priority', 'support_tickets', ['priority'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Drop 8 tables in reverse dependency order
    tables_to_drop = [
        'support_tickets',
        'notification_preferences',
        'membership_status_history',
        'event_attendance',
        'certificate_verification_records',
        'digital_member_ids',
        'document_verification_events',
        'document_versions',
    ]
    for tbl in tables_to_drop:
        if tbl in existing_tables:
            op.drop_table(tbl)

    # 2. Batch drop added columns from existing tables
    if 'member_profile_change_requests' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('member_profile_change_requests')}
        with op.batch_alter_table('member_profile_change_requests') as batch_op:
            if 'supporting_document_id' in cols:
                batch_op.drop_column('supporting_document_id')

    if 'membership_renewals' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('membership_renewals')}
        with op.batch_alter_table('membership_renewals') as batch_op:
            if 'notes' in cols:
                batch_op.drop_column('notes')
            if 'duration_years' in cols:
                batch_op.drop_column('duration_years')

    if 'certificates' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('certificates')}
        with op.batch_alter_table('certificates') as batch_op:
            for col in ('revocation_reason', 'revoked_by_id', 'revoked_at', 'status', 'certificate_type', 'title_en'):
                if col in cols:
                    batch_op.drop_column(col)

    if 'member_documents' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('member_documents')}
        with op.batch_alter_table('member_documents') as batch_op:
            for col in ('deleted_at', 'expires_at', 'verified_at', 'reviewer_note', 'version', 'file_size', 'title'):
                if col in cols:
                    batch_op.drop_column(col)

    if 'notifications' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('notifications')}
        with op.batch_alter_table('notifications') as batch_op:
            for col in ('expires_at', 'priority', 'data_json', 'body_en', 'title_en'):
                if col in cols:
                    batch_op.drop_column(col)

    if 'event_registrations' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('event_registrations')}
        with op.batch_alter_table('event_registrations') as batch_op:
            for col in ('cancellation_reason', 'cancelled_at', 'qr_token', 'waitlist_position', 'member_id'):
                if col in cols:
                    batch_op.drop_column(col)

    if 'events' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('events')}
        with op.batch_alter_table('events') as batch_op:
            for col in (
                'updated_at',
                'eligibility_criteria',
                'certificate_eligible',
                'meeting_link',
                'is_online',
                'location_en',
                'venue',
                'end_time',
                'start_time',
                'end_date',
                'start_date',
                'description_en',
                'status',
                'category',
            ):
                if col in cols:
                    batch_op.drop_column(col)
