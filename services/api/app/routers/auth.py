from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.mfa import decrypt_secret, verify_totp
from app.core.rate_limit import client_key, limiter
from app.core.security import create_token, hash_password, hash_session_token, verify_password
from app.core.tokens import hash_reset_token, random_token, reset_expiry
from app.core.deps import current_user
from app.db.session import get_db
from app.models import EmailVerificationToken, Member, PasswordResetToken, User, UserSession
from app.schemas.auth import LoginRequest, MeResponse, PasswordChangeRequest, PasswordResetConfirm, PasswordResetRequest, RegisterRequest, RegisterResponse, VerifyEmailRequest
from app.services import EmailService, audit

router = APIRouter(prefix='/auth', tags=['auth'])


def _rate_limit(request: Request, scope: str, limit: int, window: int) -> None:
    if settings.rate_limit_enabled:
        limiter.check(client_key(request, scope), limit, window)


def _issue_cookie(response: Response, db: Session, user: User) -> None:
    token, session_id = create_token(user.id)
    expires = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    db.add(UserSession(user_id=user.id, token_hash=hash_session_token(token), expires_at=expires))
    response.set_cookie(
        settings.cookie_name,
        token,
        httponly=True,
        secure=settings.app_env == 'production',
        samesite='lax',
        max_age=settings.jwt_expire_minutes * 60,
        path='/',
    )


@router.post('/register', response_model=RegisterResponse)
def register(p: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    _rate_limit(request, 'register', 5, 3600)
    email = p.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'Email already registered')
    name_bn = p.name_bn or p.fullNameBn or ''
    name_en = p.name_en or p.fullNameEn
    employee_id = p.employeeId
    designation = p.designation
    u = User(email=email, password_hash=hash_password(p.password), name_bn=name_bn, name_en=name_en, phone=p.phone, email_verified=False)
    db.add(u)
    db.flush()
    db.add(Member(user_id=u.id, employee_id=employee_id, designation_bn=designation, designation_en=designation))
    raw = random_token()
    db.add(EmailVerificationToken(user_id=u.id, token_hash=hash_reset_token(raw), expires_at=reset_expiry(settings.email_verification_hours)))
    db.commit()
    db.refresh(u)
    # Email delivery is optional in development; the token is only exposed outside production.
    from app.integrations.notifications import deliver_email
    verification_link = f"{settings.frontend_url}/verify-email?token={raw}"
    deliver_email(u.email, 'Email verification', f'আপনার অ্যাকাউন্ট যাচাই করতে লিংকে যান: {verification_link}')
    return RegisterResponse(id=u.id, email=u.email, name_bn=u.name_bn, name_en=u.name_en, role=u.role, verification_required=True, verification_token=(raw if settings.app_env != 'production' else None))


@router.post('/login')
def login(p: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    _rate_limit(request, 'login', 20, 600)
    email = p.email.lower().strip()
    u = db.scalar(select(User).where(User.email == email))
    if not u or not verify_password(p.password, u.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    if not u.is_active:
        raise HTTPException(403, 'Account is disabled')
    if settings.require_email_verification and not u.email_verified:
        raise HTTPException(403, 'Email verification required')
    if u.mfa_enabled:
        secret = decrypt_secret(u.mfa_secret_enc) or u.mfa_secret
        if not p.mfa_code:
            return {'ok': False, 'mfa_required': True, 'message': 'MFA verification required'}
        if not secret or not verify_totp(secret, p.mfa_code):
            raise HTTPException(401, 'Invalid MFA code')
    _issue_cookie(response, db, u)
    db.commit()
    return {'ok': True, 'role': u.role}


@router.post('/verify-email')
def verify_email(p: VerifyEmailRequest, db: Session = Depends(get_db)):
    record = db.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hash_reset_token(p.token), EmailVerificationToken.used_at.is_(None)))
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(400, 'Invalid or expired verification token')
    user = db.get(User, record.user_id)
    if not user or not user.is_active:
        raise HTTPException(400, 'Invalid verification request')
    user.email_verified = True
    record.used_at = datetime.utcnow()
    db.commit()
    return {'ok': True, 'message': 'Email verified successfully'}


@router.post('/resend-verification')
def resend_verification(p: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    _rate_limit(request, 'verification', 5, 3600)
    user = db.scalar(select(User).where(User.email == p.email.lower().strip()))
    payload = {'ok': True, 'message': 'If the account exists, a verification link will be issued.'}
    if not user or not user.is_active or user.email_verified:
        return payload
    db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id, EmailVerificationToken.used_at.is_(None)))
    raw = random_token()
    db.add(EmailVerificationToken(user_id=user.id, token_hash=hash_reset_token(raw), expires_at=reset_expiry(settings.email_verification_hours)))
    db.commit()
    from app.integrations.notifications import deliver_email
    verification_link = f"{settings.frontend_url}/verify-email?token={raw}"
    deliver_email(user.email, 'Email verification', f'আপনার অ্যাকাউন্ট যাচাই করতে লিংকে যান: {verification_link}')
    if settings.app_env != 'production':
        payload['verification_token'] = raw
    return payload


@router.post('/logout')
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.cookie_name)
    if token:
        session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_session_token(token), UserSession.revoked_at.is_(None)))
        if session:
            session.revoked_at = datetime.utcnow()
            db.commit()
    response.delete_cookie(settings.cookie_name, path='/')
    return {'ok': True}


@router.post('/logout-all')
def logout_all(response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)))
    db.commit()
    if response:
        response.delete_cookie(settings.cookie_name, path='/')
    return {'ok': True}


@router.get('/sessions')
def sessions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(UserSession).where(UserSession.user_id == user.id).order_by(UserSession.created_at.desc()).limit(20)).all()
    return [{'id': s.id, 'created_at': s.created_at, 'last_seen_at': s.last_seen_at, 'expires_at': s.expires_at, 'revoked': bool(s.revoked_at)} for s in rows]


@router.post('/sessions/{session_id}/revoke')
def revoke_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = db.scalar(select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user.id))
    if not session:
        raise HTTPException(404, 'Session not found')
    session.revoked_at = datetime.utcnow()
    db.commit()
    return {'ok': True}


@router.get('/me', response_model=MeResponse)
def me(user=Depends(current_user), db: Session = Depends(get_db)):
    m = db.scalar(select(Member).options(selectinload(Member.circle)).where(Member.user_id == user.id))
    c = m.circle if m else None
    return MeResponse(id=user.id, email=user.email, name_bn=user.name_bn, name_en=user.name_en, role=user.role, membership_id=m.membership_id if m else None, membership_status=m.status if m else None, designation_bn=m.designation_bn if m else None, circle_bn=c.name_bn if c else None)


@router.post('/password-reset/request')
def request_password_reset(p: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    _rate_limit(request, 'reset', 5, 3600)
    user = db.scalar(select(User).where(User.email == p.email.lower().strip()))
    if not user or not user.is_active:
        return {'ok': True, 'message': 'If the account exists, a reset link will be issued.'}
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)))
    raw = random_token()
    record = PasswordResetToken(user_id=user.id, token_hash=hash_reset_token(raw), expires_at=reset_expiry(settings.password_reset_hours))
    db.add(record)
    db.commit()
    payload = {'ok': True, 'message': 'If the account exists, a reset link will be issued.'}
    if settings.app_env != 'production':
        payload['reset_token'] = raw
    return payload


@router.post('/password-reset/confirm')
def confirm_password_reset(p: PasswordResetConfirm, db: Session = Depends(get_db)):
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_reset_token(p.token), PasswordResetToken.used_at.is_(None)))
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(400, 'Invalid or expired reset token')
    user = db.get(User, record.user_id)
    if not user or not user.is_active:
        raise HTTPException(400, 'Invalid reset request')
    user.password_hash = hash_password(p.password)
    record.used_at = datetime.utcnow()
    db.execute(delete(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)))
    db.commit()
    return {'ok': True}


@router.post('/password/change')
def change_password(p: PasswordChangeRequest, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Allow an authenticated user to change their password."""
    if not verify_password(p.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail='Current password does not match')
    
    user.password_hash = hash_password(p.new_password)
    user.updated_at = datetime.utcnow()
    
    ip_addr = request.client.host if request.client else 'unknown'
    audit(db, user, 'PASSWORD_CHANGE', 'user', user.id, ip=ip_addr)
    db.commit()
    
    # Send security notification
    EmailService.send_security_alert(
        to_email=user.email,
        name=user.name_bn or user.email,
        action_desc='পাসওয়ার্ড পরিবর্তন (Password Change)',
        time_str=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        ip_addr=ip_addr,
    )
    return {'ok': True, 'message': 'Password changed successfully'}

