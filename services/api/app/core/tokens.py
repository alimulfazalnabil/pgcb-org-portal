import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from app.core.config import settings


def random_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def reset_expiry(hours: int = 2) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours)
