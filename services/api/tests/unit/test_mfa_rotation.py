import pytest
from cryptography.fernet import Fernet
from app.core.config import Settings
from app.core.mfa import generate_secret, encrypt_secret, decrypt_secret, _legacy_derived_fernet
import app.core.mfa as mfa_module


def test_mfa_legacy_encryption_and_decryption():
    secret = generate_secret()
    # Ensure mfa_encryption_key is None
    original_key = mfa_module.settings.mfa_encryption_key
    try:
        mfa_module.settings.mfa_encryption_key = None
        encrypted = encrypt_secret(secret)
        decrypted = decrypt_secret(encrypted)
        assert decrypted == secret
    finally:
        mfa_module.settings.mfa_encryption_key = original_key


def test_mfa_key_rotation_with_backward_compatibility():
    secret = generate_secret()
    original_key = mfa_module.settings.mfa_encryption_key

    try:
        # 1. Encrypt secret with legacy derived key
        mfa_module.settings.mfa_encryption_key = None
        legacy_ciphertext = encrypt_secret(secret)

        # 2. Rotate to a new dedicated Fernet key
        new_fernet_key = Fernet.generate_key().decode()
        mfa_module.settings.mfa_encryption_key = new_fernet_key

        # 3. Old secret must still decrypt successfully via the fallback
        assert decrypt_secret(legacy_ciphertext) == secret

        # 4. New secret encrypted with new key must decrypt successfully
        new_secret = generate_secret()
        new_ciphertext = encrypt_secret(new_secret)
        assert decrypt_secret(new_ciphertext) == new_secret

    finally:
        mfa_module.settings.mfa_encryption_key = original_key


def test_invalid_mfa_encryption_key_rejected():
    with pytest.raises(ValueError, match="MFA_ENCRYPTION_KEY is invalid"):
        Settings(
            app_env="production",
            jwt_secret="a-valid-random-32-character-secret-key-12345",
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            mfa_encryption_key="invalid-non-base64-key",
        )
