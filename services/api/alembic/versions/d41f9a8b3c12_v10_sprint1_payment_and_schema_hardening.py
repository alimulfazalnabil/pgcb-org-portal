"""v1.0 sprint 1 payment idempotency, plan_id, and schema constraints"""
from alembic import op
import sqlalchemy as sa

revision = 'd41f9a8b3c12'
down_revision = 'c2048b9f1d09'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'security_audit_logs' not in existing_tables:
        op.create_table(
            'security_audit_logs',
            sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('role', sa.String(), nullable=True),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('entity', sa.String(), nullable=True),
            sa.Column('entity_id', sa.String(), nullable=True),
            sa.Column('old_value', sa.JSON(), nullable=True),
            sa.Column('new_value', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(), nullable=True),
            sa.Column('user_agent', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_security_audit_logs_action', 'security_audit_logs', ['action'], unique=False)
        op.create_index('ix_security_audit_logs_entity', 'security_audit_logs', ['entity'], unique=False)
        op.create_index('ix_security_audit_logs_entity_id', 'security_audit_logs', ['entity_id'], unique=False)
        op.create_index('ix_security_audit_logs_timestamp', 'security_audit_logs', ['timestamp'], unique=False)

    if 'gateway_payment_transactions' not in existing_tables:
        op.create_table(
            'gateway_payment_transactions',
            sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='SET NULL'), nullable=True),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('provider', sa.String(length=40), nullable=False),
            sa.Column('provider_transaction_id', sa.String(), nullable=True),
            sa.Column('status', sa.String(length=40), nullable=True),
            sa.Column('reference', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
        )
        op.create_index(
            'ix_gateway_payment_transactions_provider_transaction_id',
            'gateway_payment_transactions',
            ['provider_transaction_id'],
            unique=True,
        )
        op.create_index('ix_gateway_payment_transactions_status', 'gateway_payment_transactions', ['status'], unique=False)
        op.create_index('ix_gateway_payment_transactions_reference', 'gateway_payment_transactions', ['reference'], unique=False)

    if 'payment_webhooks' not in existing_tables:
        op.create_table(
            'payment_webhooks',
            sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('provider', sa.String(length=40), nullable=False),
            sa.Column('transaction_id', sa.Uuid(as_uuid=True), sa.ForeignKey('gateway_payment_transactions.id'), nullable=True),
            sa.Column('payload', sa.JSON(), nullable=False),
            sa.Column('is_processed', sa.Boolean(), nullable=True),
            sa.Column('received_at', sa.DateTime(), nullable=True),
        )

    existing_pt_cols = {c['name'] for c in inspector.get_columns('payment_transactions')}
    with op.batch_alter_table('payment_transactions') as batch_op:
        if 'membership_plan_id' not in existing_pt_cols:
            batch_op.add_column(sa.Column('membership_plan_id', sa.String(length=80), nullable=True))
        if 'provider_transaction_id' not in existing_pt_cols:
            batch_op.add_column(sa.Column('provider_transaction_id', sa.String(length=160), nullable=True))
        if 'idempotency_key' not in existing_pt_cols:
            batch_op.add_column(sa.Column('idempotency_key', sa.String(length=180), nullable=True))
        batch_op.create_index('ix_payment_transactions_membership_plan_id', ['membership_plan_id'], unique=False)
        batch_op.create_index('ix_payment_transactions_provider_transaction_id', ['provider_transaction_id'], unique=True)
        batch_op.create_index('ix_payment_transactions_idempotency_key', ['idempotency_key'], unique=True)
        batch_op.create_unique_constraint('uq_payment_transactions_transaction_ref', ['transaction_ref'])

    with op.batch_alter_table('members') as batch_op:
        batch_op.create_index('ix_members_nid_number', ['nid_number'], unique=False)


def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_index('ix_members_nid_number')

    with op.batch_alter_table('payment_transactions') as batch_op:
        batch_op.drop_constraint('uq_payment_transactions_transaction_ref', type_='unique')
        batch_op.drop_index('ix_payment_transactions_idempotency_key')
        batch_op.drop_index('ix_payment_transactions_provider_transaction_id')
        batch_op.drop_index('ix_payment_transactions_membership_plan_id')
        batch_op.drop_column('idempotency_key')
        batch_op.drop_column('provider_transaction_id')
        batch_op.drop_column('membership_plan_id')

