from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.db.session import get_db
from app.models.payments import PaymentTransaction, PaymentWebhook, PaymentStatus, PaymentProviderType
from app.models import Event, EventRegistration, Member, User, PaymentTransaction as CorePaymentTransaction
from app.schemas.events import PaymentCreate
from app.core.audit import log_audit_action
from app.integrations.payments import get_payment_provider, create_checkout, normalize_provider

router = APIRouter(tags=["Payments"])


# ==========================================================
# 1. Asynchronous Gateway Webhook Receiver (Phase 10 Spec)
# ==========================================================

@router.post("/payments/webhook/{provider}")
@router.post("/webhook/{provider}")
async def handle_payment_webhook(
    provider: PaymentProviderType,
    request: Request,
    x_signature: str | None = Header(None),  # bKash / SSLCommerz signature header
    db: Session = Depends(get_db)
):
    """Idempotent webhook receiver for payment gateways."""
    payload = await request.json()

    # 1. Log the raw webhook immediately for audit and replayability
    webhook_log = PaymentWebhook(provider=provider, payload=payload)
    db.add(webhook_log)
    db.commit()
    db.refresh(webhook_log)

    # 2. Get the specific payment provider implementation
    payment_service = get_payment_provider(provider.value)

    # 3. Verify Signature & Parse
    is_valid, provider_trx_id, gateway_status = payment_service.parse_webhook(payload, x_signature)

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # 4. Idempotency Check & Transaction Update
    transaction = db.scalar(
        select(PaymentTransaction).where(
            PaymentTransaction.provider_transaction_id == provider_trx_id
        )
    )

    if not transaction and payload.get("payment_id"):
        # Fallback to internal ID if provided in return metadata
        try:
            transaction = db.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.id == payload["payment_id"]
                )
            )
        except Exception:
            pass

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status in (PaymentStatus.PAID, "PAID"):
        # Idempotent return: already processed
        return {"status": "already_processed"}

    if gateway_status == "SUCCESS":
        # Double check with a synchronous server-to-server verification call
        if payment_service.verify_payment(provider_trx_id):
            transaction.status = PaymentStatus.PAID
            transaction.completed_at = datetime.utcnow()
            webhook_log.is_processed = True
            webhook_log.transaction_id = transaction.id
            db.commit()

            # Record security audit log
            log_audit_action(
                db, request,
                action="PAYMENT_COMPLETED",
                entity="PAYMENT",
                entity_id=str(transaction.id),
                new_value={"provider": provider.value, "trx_id": provider_trx_id, "amount": transaction.amount}
            )

            # Dispatch Celery background task to send Payment Receipt Email
            try:
                from app.worker import send_receipt_task
                if send_receipt_task:
                    send_receipt_task.delay(str(transaction.id))
            except Exception:
                pass

            return {"status": "success"}

    return {"status": "ignored"}


# ==========================================================
# 2. Member Checkout & Payment Operations (Portal Integration)
# ==========================================================

@router.post("/member/payments")
def create_payment(payload: PaymentCreate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    registration = None
    if payload.event_registration_id:
        registration = db.scalar(
            select(EventRegistration).where(
                EventRegistration.id == payload.event_registration_id,
                EventRegistration.user_id == user.id
            )
        )
        if not registration:
            raise HTTPException(404, 'Event registration not found')
        event = db.get(Event, registration.event_id)
        if not event or not event.fee_amount:
            raise HTTPException(409, 'No payment is required for this event')
        if payload.amount != event.fee_amount:
            raise HTTPException(400, 'Payment amount does not match event fee')
        registration.payment_status = 'PENDING'
    elif payload.purpose == 'MEMBERSHIP':
        if not member:
            raise HTTPException(404, 'Member profile not found')

    item = CorePaymentTransaction(
        user_id=user.id,
        member_id=member.id if member else None,
        event_registration_id=payload.event_registration_id,
        amount=int(payload.amount),
        currency=payload.currency.upper(),
        provider=payload.provider.upper() if payload.provider else 'MANUAL',
        purpose=payload.purpose.upper() if payload.purpose else 'MEMBERSHIP',
        transaction_ref=payload.transaction_ref,
        status='PENDING'
    )
    db.add(item)
    db.flush()

    log_audit_action(
        db, request,
        action="CREATE_PAYMENT",
        entity="PAYMENT",
        entity_id=str(item.id),
        user=user,
        new_value={"amount": item.amount, "currency": item.currency, "provider": str(item.provider)}
    )
    db.commit()
    db.refresh(item)

    return {
        'id': item.id,
        'status': item.status,
        'amount': item.amount,
        'currency': item.currency,
        'provider': item.provider,
        'transaction_ref': item.transaction_ref,
        'message': 'Payment intent created. Connect a configured gateway or submit transaction reference for verification.'
    }


@router.post("/member/payments/checkout")
@router.post("/payments/checkout")
def create_checkout_intent(payload: PaymentCreate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    provider = normalize_provider(payload.provider)
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    registration = None
    if payload.event_registration_id:
        registration = db.scalar(
            select(EventRegistration).where(
                EventRegistration.id == payload.event_registration_id,
                EventRegistration.user_id == user.id
            )
        )
        if not registration:
            raise HTTPException(404, 'Event registration not found')
        event = db.get(Event, registration.event_id)
        if not event or not event.fee_amount or payload.amount != event.fee_amount:
            raise HTTPException(400, 'Payment amount does not match event fee')
    elif payload.purpose == 'MEMBERSHIP' and not member:
        raise HTTPException(404, 'Member profile not found')

    provider_enum = PaymentProviderType[provider] if provider in PaymentProviderType.__members__ else PaymentProviderType.TEST

    item = CorePaymentTransaction(
        user_id=user.id,
        member_id=member.id if member else None,
        event_registration_id=registration.id if registration else None,
        amount=float(payload.amount),
        currency=payload.currency.upper(),
        provider=provider,
        purpose=payload.purpose.upper(),
        status='PENDING'
    )
    db.add(item)
    db.flush()

    checkout = create_checkout(provider, 1, float(item.amount), item.currency)
    item.transaction_ref = checkout.provider_transaction_id

    if registration and registration.payment_status == 'NOT_REQUIRED':
        registration.payment_status = 'PENDING'

    log_audit_action(
        db, request,
        action="CREATE_CHECKOUT",
        entity="PAYMENT",
        entity_id=str(item.id),
        user=user,
        new_value={"provider": provider, "trx_id": checkout.provider_transaction_id, "amount": float(item.amount)}
    )
    db.commit()
    db.refresh(item)

    return {
        'payment_id': item.id,
        'provider': provider,
        'provider_transaction_id': checkout.provider_transaction_id,
        'checkout_url': checkout.checkout_url,
        'status': item.status,
        'amount': float(item.amount),
        'currency': item.currency
    }


@router.get("/member/payments")
def list_payments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    member_id = member.id if member else None
    
    rows = db.scalars(
        select(CorePaymentTransaction)
        .where(CorePaymentTransaction.member_id == member_id)
        .order_by(CorePaymentTransaction.created_at.desc())
    ).all() if member_id else []

    return [
        {
            'id': p.id,
            'purpose': p.purpose or 'MEMBERSHIP',
            'amount': float(p.amount),
            'currency': p.currency,
            'provider': p.provider,
            'transaction_ref': p.transaction_ref,
            'status': p.status,
            'created_at': p.created_at
        }
        for p in rows
    ]
