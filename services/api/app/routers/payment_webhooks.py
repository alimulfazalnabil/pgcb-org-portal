from __future__ import annotations

import json
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import client_key, limiter
from app.core.config import settings
from app.db.session import get_db
from app.integrations.payments import get_payment_provider, parse_webhook, payment_status_from_provider, verify_hmac_signature
from app.models import EventRegistration, PaymentTransaction, PaymentWebhookEvent
from app.services.receipt_service import activate_membership_from_payment, ensure_receipt_metadata

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
    if provider_txn:
        payment.transaction_ref = provider_txn

    if status == 'PAID':
        # Server-to-server gateway verification & amount check
        try:
            gw = get_payment_provider(provider)
            trx_to_verify = provider_txn or payment.transaction_ref or ''
            if not gw.verify_payment(trx_to_verify, expected_amount=float(payment.amount)):
                status = 'FAILED'
        except ValueError:
            pass

    if status:
        payment.status = status

    if status == 'PAID':
        ensure_receipt_metadata(payment)
        if payment.event_registration_id:
            registration = db.get(EventRegistration, payment.event_registration_id)
            if registration:
                registration.payment_status = 'PAID'
        if payment.purpose in {'MEMBERSHIP', 'RENEWAL', 'APPLICATION'}:
            activate_membership_from_payment(db, payment)

    event.processing_status = 'PROCESSED'
    event.processed_at = datetime.utcnow()
    db.commit()
    return {
        'ok': True,
        'matched': True,
        'payment_id': payment.id,
        'status': payment.status,
        'receipt_no': payment.receipt_no,
    }
