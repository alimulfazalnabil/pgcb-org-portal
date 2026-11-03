import pytest
from sqlalchemy import select
from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models import User
from app.scripts.create_admin import bootstrap_admin, validate_admin_credentials


def test_validate_admin_credentials_rejects_unsafe_passwords():
    # Test rejection of known unsafe default passwords
    for unsafe in ["Secret", "admin", "password", "changeme123!", "12345678", "mystrongpassword123!"]:
        with pytest.raises(ValueError, match="Unsafe default password rejected"):
            validate_admin_credentials("admin@pgcbportal.org.bd", unsafe, is_prod=False)


def test_validate_admin_credentials_rejects_invalid_email():
    with pytest.raises(ValueError, match="Invalid administrator email"):
        validate_admin_credentials("not-an-email", "ValidStrongPassword2026!", is_prod=False)


def test_validate_admin_credentials_rejects_placeholder_domain_in_production():
    with pytest.raises(ValueError, match="Unsafe placeholder email domain"):
        validate_admin_credentials("admin@example.org", "ValidStrongPassword2026!", is_prod=True)


def test_validate_admin_credentials_accepts_strong_credentials():
    # Should not raise
    validate_admin_credentials("secretariat@pgcbportal.org.bd", "ValidStrongPassword2026!", is_prod=True)


def test_bootstrap_admin_creates_and_preserves_password():
    test_email = "bootstrap_test_admin@pgcbportal.org.bd"
    initial_pw = "InitialStrongPassword2026!"
    second_pw = "SecondDifferentPassword2026!"

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == test_email))
        if existing:
            db.delete(existing)
            db.commit()

    try:
        # 1. Create initial admin
        admin1 = bootstrap_admin(test_email, initial_pw, name="Admin One")
        assert admin1.role == "SUPER_ADMIN"
        assert admin1.is_active is True
        assert admin1.email_verified is True
        initial_hash = admin1.password_hash
        assert verify_password(initial_pw, initial_hash)

        # 2. Re-run bootstrap without force_reset_password: MUST PRESERVE initial password
        admin2 = bootstrap_admin(test_email, second_pw, name="Admin One Updated")
        assert admin2.id == admin1.id
        assert admin2.password_hash == initial_hash
        assert verify_password(initial_pw, admin2.password_hash)
        assert not verify_password(second_pw, admin2.password_hash)

        # 3. Re-run bootstrap with force_reset_password=True: MUST UPDATE password
        admin3 = bootstrap_admin(test_email, second_pw, force_reset_password=True)
        assert admin3.id == admin1.id
        assert admin3.password_hash != initial_hash
        assert verify_password(second_pw, admin3.password_hash)

    finally:
        with SessionLocal() as db:
            to_clean = db.scalar(select(User).where(User.email == test_email))
            if to_clean:
                db.delete(to_clean)
                db.commit()
