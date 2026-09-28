from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.domain.membership import (
    resolve_server_payment_amount,
    can_transition_payment_status,
    can_transition_member_status,
    generate_receipt_number,
)


def test_password_hashing_and_jwt_roundtrip():
    raw = 'PgcbPortalUnitPass123!'
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password('WrongPass123!', hashed) is False

    token = create_access_token('unit_member@pgcb.gov.bd', extra_claims={'role': 'MEMBER'})
    payload = decode_token(token)
    assert payload is not None
    assert payload['sub'] == 'unit_member@pgcb.gov.bd'
    assert payload['role'] == 'MEMBER'


def test_server_authoritative_pricing_and_state_machines():
    amount, currency, code = resolve_server_payment_amount(
        purpose='MEMBERSHIP',
        membership_plan_id='ANNUAL_STANDARD',
    )
    assert amount == 1000
    assert currency == 'BDT'
    assert code == 'ANNUAL_STANDARD'

    assert can_transition_payment_status('PENDING', 'PAID') is True
    assert can_transition_payment_status('PAID', 'PENDING') is False
    assert can_transition_member_status('PENDING', 'UNDER_REVIEW') is True
    assert can_transition_member_status('UNDER_REVIEW', 'APPROVED') is True
    assert can_transition_member_status('APPROVED', 'ACTIVE') is True

    rcp = generate_receipt_number(42)
    assert rcp.startswith('PGCB-RCP-')


def test_production_origin_normalization_strips_legacy_render_assumptions():
    assert settings.payment_mode in ('sandbox', 'production', 'live')
    assert '.onrender.com' not in (settings.frontend_url or '')
