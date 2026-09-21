from __future__ import annotations

import json
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import client_key, limiter
from app.core.config import settings
from app.db.session import get_db
from app.integrations.payments import parse_webhook, payment_status_from_provider, verify_hmac_signature
from app.models import EventRegistration, PaymentTransaction, PaymentWebhookEvent, Member, User, Notification, MembershipRenewal
from app.domain.membership import renew_membership

router = APIRouter(prefix='/payments/webhooks', tags=['payment-webhooks'])


@router.post('/{provider}')
async def receive_webhook(provider: str, request: Request, x_signature: str | None = Header(default=None), x_event_id: str | None = Header(default=None), db: Session = Depends(get_db)):
    # Dependency injection kept explicit to make raw-body signature validation deterministic.
    body = await request.body()
    if settings.rate_limit_enabled:
        limiter.check(client_key(request, f'webhook-{provider}'), 120, 60)
    signature_valid = verify_hmac_signature(provider, body, x_signature)
    if not signature_valid:
        raise HTTPException(401, 'Invalid webhook signature')
    try:
        payload = json.loads(body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(400, 'Invalid JSON payload')
    event_id, provider_txn, raw_status = parse_webhook(payload)
    event_id = event_id or x_event_id
    if not event_id:
        raise HTTPException(400, 'Missing event id')
    existing = db.scalar(select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_id == event_id))
    if existing:
        return {'ok': True, 'duplicate': True, 'status': existing.processing_status}

    event = PaymentWebhookEvent(provider=provider.upper(), event_id=event_id, event_type=str(payload.get('event_type') or payload.get('type') or 'payment'), signature_valid=True, payload=payload, processing_status='RECEIVED')
    db.add(event)
    status = payment_status_from_provider(raw_status)
    payment = None
    if provider_txn:
        payment = db.scalar(select(PaymentTransaction).where(PaymentTransaction.transaction_ref == provider_txn))
    if not payment and payload.get('payment_id'):
        payment = db.get(PaymentTransaction, int(payload['payment_id']))
    if not payment:
        event.processing_status = 'UNMATCHED'
        event.processed_at = datetime.utcnow()
        db.commit()
        return {'ok': True, 'matched': False}

    event.payment_id = payment.id
    if status:
        payment.status = status
    if provider_txn:
        payment.transaction_ref = provider_txn

    if status == 'PAID':
        if payment.event_registration_id:
            registration = db.get(EventRegistration, payment.event_registration_id)
            if registration:
                registration.payment_status = 'PAID'
        if payment.member_id and payment.purpose == 'MEMBERSHIP':
            member = db.get(Member, payment.member_id)
            user = db.get(User, member.user_id) if member else None
            if member:
                existing_renewal = db.scalar(select(MembershipRenewal).where(MembershipRenewal.payment_id == payment.id))
                if not existing_renewal:
                    renew_membership(db, member, payment.id, payment.amount, payment.currency)
                    if user:
                        db.add(Notification(user_id=user.id, title_bn='সদস্যতা নবায়ন সফল', body_bn='আপনার সদস্যতা সফলভাবে নবায়ন করা হয়েছে।', notification_type='MEMBERSHIP'))
    event.processing_status = 'PROCESSED'
    event.processed_at = datetime.utcnow()
    db.commit()
    return {'ok': True, 'matched': True, 'payment_id': payment.id, 'status': payment.status}
