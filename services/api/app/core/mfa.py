from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def generate_secret(length: int = 20) -> str:
    return base64.b32encode(secrets.token_bytes(length)).decode().rstrip('=')


def _hotp(secret: str, counter: int) -> str:
    padded = secret + '=' * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    msg = struct.pack('>Q', counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f'{code:06d}'


def totp_code(secret: str, now: int | None = None) -> str:
    current = int((now or time.time()) // 30)
    return _hotp(secret, current)


def verify_totp(secret: str, code: str, window: int = 1, now: int | None = None) -> bool:
    if not secret or not code or len(code) != 6 or not code.isdigit():
        return False
    current = int((now or time.time()) // 30)
    return any(hmac.compare_digest(_hotp(secret, current + delta), code) for delta in range(-window, window + 1))


def otpauth_uri(secret: str, email: str, issuer: str = 'PGCB Organization Portal') -> str:
    label = quote(f'{issuer}:{email}')
    issuer_q = quote(issuer)
    return f'otpauth://totp/{label}?secret={secret}&issuer={issuer_q}&algorithm=SHA1&digits=6&period=30'


def _fernet() -> Fernet:
    configured = settings.mfa_encryption_key
    if configured:
        return Fernet(configured.encode())
    derived = base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret.encode()).digest())
    return Fernet(derived)


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError, TypeError):
        return None


def _hash_backup_code(code: str) -> str:
    normalized = code.strip().upper().replace(" ", "")
    return hashlib.sha256(f"{settings.jwt_secret}:{normalized}".encode()).hexdigest()


def generate_backup_codes(db: Session, user_id: int, count: int = 8) -> list[str]:
    """Generate and persist hashed single-use MFA recovery backup codes for a user."""
    from app.models import SiteSetting

    raw_codes: list[str] = []
    hashed_codes: list[str] = []
    for _ in range(count):
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        raw = f"PGCB-{part1}-{part2}"
        raw_codes.append(raw)
        hashed_codes.append(_hash_backup_code(raw))

    key = f"mfa_backup_codes_user_{user_id}"
    setting = db.scalar(select(SiteSetting).where(SiteSetting.key == key))
    if setting:
        setting.value = json.dumps(hashed_codes)
    else:
        db.add(SiteSetting(key=key, value=json.dumps(hashed_codes), category="SECURITY"))
    db.flush()
    return raw_codes


def consume_backup_code(db: Session, user_id: int, code: str) -> bool:
    """Verify and consume a single-use MFA backup code."""
    from app.models import SiteSetting

    if not code or len(code.strip()) < 6:
        return False
    key = f"mfa_backup_codes_user_{user_id}"
    setting = db.scalar(select(SiteSetting).where(SiteSetting.key == key))
    if not setting or not setting.value:
        return False
    try:
        hashes: list[str] = json.loads(setting.value)
    except Exception:
        return False
    candidate = _hash_backup_code(code)
    for idx, stored in enumerate(hashes):
        if hmac.compare_digest(stored, candidate):
            hashes.pop(idx)
            setting.value = json.dumps(hashes)
            db.flush()
            return True
    return False
