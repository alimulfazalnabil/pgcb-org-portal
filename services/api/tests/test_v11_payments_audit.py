import pytest
from app.integrations.payments import get_payment_provider, PaymentProvider, SSLCommerzProvider, BKashProvider, TestProvider
from app.core.audit import log_audit_action, AuditLog
from app.db.session import SessionLocal, Base, engine


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_payment_provider_factory():
    p_sslc = get_payment_provider("SSLCOMMERZ")
    assert isinstance(p_sslc, PaymentProvider)
    assert isinstance(p_sslc, SSLCommerzProvider)

    p_bkash = get_payment_provider("BKASH")
    assert isinstance(p_bkash, PaymentProvider)
    assert isinstance(p_bkash, BKashProvider)

    p_test = get_payment_provider("TEST")
    assert isinstance(p_test, PaymentProvider)
    assert isinstance(p_test, TestProvider)

    with pytest.raises(ValueError):
        get_payment_provider("UNSUPPORTED_GATEWAY")


def test_test_provider_payment_flow():
    provider = get_payment_provider("TEST")
    checkout = provider.create_payment(amount=500.0, reference="MEMBERSHIP-2026", return_url="/portal")
    assert "trx_id" in checkout
    assert "checkout_url" in checkout
    assert checkout["amount"] == 500.0

    is_valid, trx_id, status = provider.parse_webhook({"trx_id": checkout["trx_id"]}, signature=None)
    assert is_valid is True
    assert status == "SUCCESS"
    assert provider.verify_payment(trx_id) is True


def test_audit_log_strips_passwords():
    db = SessionLocal()
    try:
        log_audit_action(
            db,
            request=None,
            action="SECURITY_TEST",
            entity="USER",
            entity_id="999",
            old_value={"username": "test_engineer", "password": "sensitive_raw_password"},
            new_value={"status": "ACTIVE", "token": "secret_session_token"}
        )
        entry = db.query(AuditLog).filter(AuditLog.action == "SECURITY_TEST").first()
        assert entry is not None
        assert "password" not in (entry.old_value or {})
        assert "token" not in (entry.new_value or {})
        assert entry.old_value.get("username") == "test_engineer"
    finally:
        db.close()
