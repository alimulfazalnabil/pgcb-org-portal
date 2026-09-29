from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token_payload
from app.domain.membership import resolve_renewal_days
from app.services.payment_service import validate_payment_transition
from app.services.receipt_service import MEMBERSHIP_PLAN_FEES


def test_password_hashing_and_jwt_roundtrip():
    raw = 'PgcbPortalUnitPass123!'
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password('WrongPass123!', hashed) is False

    token = create_access_token('42', roles=['MEMBER'])
    payload = decode_token_payload(token)
    assert payload is not None
    assert payload['sub'] == '42'
    assert 'MEMBER' in payload['roles']


def test_server_authoritative_pricing_and_state_machines():
    assert MEMBERSHIP_PLAN_FEES['ANNUAL_STANDARD'] == 2000
    assert MEMBERSHIP_PLAN_FEES['LIFE'] == 10000

    assert resolve_renewal_days('ANNUAL_STANDARD') == 365
    assert resolve_renewal_days('RENEWAL_2YR') == 730
    assert resolve_renewal_days('LIFE') == 18250

    assert validate_payment_transition('PENDING', 'PAID') is True
    assert validate_payment_transition('PAID', 'PENDING') is False


def test_application_state_machine_transitions():
    from app.services.membership_service import APPLICATION_STATES, validate_application_transition

    assert set(APPLICATION_STATES) == {
        'DRAFT',
        'SUBMITTED',
        'UNDER_REVIEW',
        'CORRECTION_REQUIRED',
        'APPROVED',
        'PAYMENT_PENDING',
        'ACTIVE',
        'REJECTED',
        'CANCELLED',
    }
    assert validate_application_transition('DRAFT', 'SUBMITTED') is True
    assert validate_application_transition('SUBMITTED', 'UNDER_REVIEW') is True
    assert validate_application_transition('UNDER_REVIEW', 'CORRECTION_REQUIRED') is True
    assert validate_application_transition('CORRECTION_REQUIRED', 'SUBMITTED') is True
    assert validate_application_transition('UNDER_REVIEW', 'PAYMENT_PENDING') is True
    assert validate_application_transition('PAYMENT_PENDING', 'ACTIVE') is True
    assert validate_application_transition('ACTIVE', 'DRAFT') is False


def test_production_origin_normalization_strips_legacy_render_assumptions():
    assert settings.payment_mode in ('sandbox', 'production', 'live')
    assert '.onrender.com' not in (settings.frontend_url or '')
