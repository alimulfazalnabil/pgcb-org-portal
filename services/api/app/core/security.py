from datetime import datetime, timedelta
from typing import Any, Union
import hashlib
import os
import uuid

try:
    from jose import jwt
except ImportError:
    import jwt
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
except ImportError:
    pwd_context = None

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-development-key-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TTL", 30))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if pwd_context is not None:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    # Fallback to legacy scrypt for demo accounts if present
    try:
        import base64, hmac
        s, d = hashed_password.split('.', 1)
        salt = base64.b64decode(s)
        expected = base64.b64decode(d)
        actual = hashlib.scrypt(plain_password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    if pwd_context is not None:
        return pwd_context.hash(password)
    import base64
    salt = os.urandom(16)
    hashed = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{base64.b64encode(salt).decode('utf-8')}.{base64.b64encode(hashed).decode('utf-8')}"


# Backward-compatible alias for existing callers
hash_password = get_password_hash


def create_access_token(subject: Union[str, Any], roles: list[str] | None = None) -> str:
    roles = roles or []
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "roles": roles}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token(user_id: int | str, jti: str | None = None, roles: list[str] | None = None) -> tuple[str, str]:
    session_id = jti or uuid.uuid4().hex
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "jti": session_id,
        "roles": roles or ["MEMBER"]
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, session_id


def decode_token_payload(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


def decode_token(token: str) -> int | None:
    payload = decode_token_payload(token)
    if not payload or not payload.get("sub"):
        return None
    try:
        return int(payload["sub"])
    except (ValueError, TypeError):
        return None


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
