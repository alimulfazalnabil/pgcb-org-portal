from __future__ import annotations

from datetime import datetime
from typing import Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import SECRET_KEY, ALGORITHM, decode_token_payload, hash_session_token
from app.db.session import SessionLocal, get_db
from app.models.core import User, UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _resolve_token(request: Request, bearer_token: str | None = None) -> str | None:
    if bearer_token:
        return bearer_token
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return request.cookies.get(settings.cookie_name)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    bearer_token: str | None = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = _resolve_token(request, bearer_token)
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        uid = int(user_id)
        user = db.get(User, uid)
    except (ValueError, TypeError):
        user = db.query(User).filter(User.email == str(user_id)).first()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    session_hash = hash_session_token(token)
    session_row = db.scalar(select(UserSession).where(UserSession.token_hash == session_hash))
    if session_row:
        if session_row.revoked_at is not None:
            raise credentials_exception
        if session_row.expires_at < datetime.utcnow():
            raise credentials_exception

    return user


# Backward-compatible alias for existing routers
current_user = get_current_user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request, bearer_token: str | None = Depends(oauth2_scheme)):
        token = _resolve_token(request, bearer_token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_roles: list[str] = payload.get("roles", [])

            # Check if user has any of the required roles, or if they are a SUPER_ADMIN
            if "SUPER_ADMIN" in user_roles:
                return True

            if not any(role in self.allowed_roles for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operation not permitted for your role",
                )
            return True
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


def require_roles(*roles: str):
    def d(user: User = Depends(get_current_user)):
        if user.role != "SUPER_ADMIN" and user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return d
