"""v0.5 operations: sessions, event registrations, payments, notification deliveries"""
from alembic import op
import sqlalchemy as sa

revision = 'cd57f8a2e1b9'
down_revision = 'ab42d1ef6c70'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('mfa_secret_enc', sa.String(length=512), nullable=True))

    op.add_column('events', sa.Column('capacity', sa.Integer(), nullable=True))
    op.add_column('events', sa.Column('registration_deadline', sa.DateTime(), nullable=True))
    op.add_column('events', sa.Column('fee_amount', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('events', sa.Column('fee_currency', sa.String(length=10), nullable=False, server_default='BDT'))

    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['token_hash'], unique=True)
    op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('ix_user_sessions_created_at', 'user_sessions', ['created_at'])

    op.create_table(
        'event_registrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('organization', sa.String(length=250), nullable=True),
        sa.Column('ticket_code', sa.String(length=80), nullable=False),
        sa.Column('registration_status', sa.String(length=30), nullable=False),
        sa.Column('attendance_status', sa.String(length=30), nullable=False),
        sa.Column('payment_status', sa.String(length=30), nullable=False),
        sa.Column('registered_at', sa.DateTime(), nullable=False),
        sa.Column('checked_in_at', sa.DateTime(), nullable=True),
        sa.Column('checked_in_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['checked_in_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_code'),
        sa.UniqueConstraint('event_id', 'email', name='uq_event_registration_email'),
    )
    for name, column, unique in [
        ('ix_event_registrations_event_id', 'event_id', False),
        ('ix_event_registrations_user_id', 'user_id', False),
        ('ix_event_registrations_email', 'email', False),
        ('ix_event_registrations_ticket_code', 'ticket_code', True),
        ('ix_event_registrations_registration_status', 'registration_status', False),
        ('ix_event_registrations_attendance_status', 'attendance_status', False),
        ('ix_event_registrations_payment_status', 'payment_status', False),
        ('ix_event_registrations_registered_at', 'registered_at', False),
    ]:
        op.create_index(name, 'event_registrations', [column], unique=unique)

    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('event_registration_id', sa.Integer(), nullable=True),
        sa.Column('purpose', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('provider', sa.String(length=40), nullable=False),
        sa.Column('transaction_ref', sa.String(length=120), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('provider_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['event_registration_id'], ['event_registrations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    for name, column in [
        ('ix_payment_transactions_user_id', 'user_id'),
        ('ix_payment_transactions_member_id', 'member_id'),
        ('ix_payment_transactions_event_registration_id', 'event_registration_id'),
        ('ix_payment_transactions_purpose', 'purpose'),
        ('ix_payment_transactions_transaction_ref', 'transaction_ref'),
        ('ix_payment_transactions_status', 'status'),
        ('ix_payment_transactions_created_at', 'created_at'),
    ]:
        op.create_index(name, 'payment_transactions', [column])

    op.create_table(
        'notification_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_message_id', sa.String(length=200), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    for name, column in [
        ('ix_notification_deliveries_notification_id', 'notification_id'),
        ('ix_notification_deliveries_channel', 'channel'),
        ('ix_notification_deliveries_status', 'status'),
        ('ix_notification_deliveries_created_at', 'created_at'),
    ]:
        op.create_index(name, 'notification_deliveries', [column])


def downgrade():
    for name in ['ix_notification_deliveries_created_at', 'ix_notification_deliveries_status', 'ix_notification_deliveries_channel', 'ix_notification_deliveries_notification_id']:
        op.drop_index(name, table_name='notification_deliveries')
    op.drop_table('notification_deliveries')

    for name in ['ix_payment_transactions_created_at', 'ix_payment_transactions_status', 'ix_payment_transactions_transaction_ref', 'ix_payment_transactions_purpose', 'ix_payment_transactions_event_registration_id', 'ix_payment_transactions_member_id', 'ix_payment_transactions_user_id']:
        op.drop_index(name, table_name='payment_transactions')
    op.drop_table('payment_transactions')

    for name in ['ix_event_registrations_registered_at', 'ix_event_registrations_payment_status', 'ix_event_registrations_attendance_status', 'ix_event_registrations_registration_status', 'ix_event_registrations_ticket_code', 'ix_event_registrations_email', 'ix_event_registrations_user_id', 'ix_event_registrations_event_id']:
        op.drop_index(name, table_name='event_registrations')
    op.drop_table('event_registrations')

    for name in ['ix_user_sessions_created_at', 'ix_user_sessions_expires_at', 'ix_user_sessions_token_hash', 'ix_user_sessions_user_id']:
        op.drop_index(name, table_name='user_sessions')
    op.drop_table('user_sessions')

    op.drop_column('events', 'fee_currency')
    op.drop_column('events', 'fee_amount')
    op.drop_column('events', 'registration_deadline')
    op.drop_column('events', 'capacity')
    op.drop_column('users', 'mfa_secret_enc')
