from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken

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
