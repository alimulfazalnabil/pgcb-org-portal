from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import current_user
from app.db.session import get_db
from app.models.payments import PaymentTransaction, PaymentWebhook, PaymentStatus, PaymentProviderType
from app.models import Event, EventRegistration, Member, User, PaymentTransaction as CorePaymentTransaction
from app.schemas.events import PaymentCreate
from app.core.audit import log_audit_action
from app.integrations.payments import get_payment_provider, create_checkout, normalize_provider
from app.services.receipt_service import (
    activate_membership_from_payment,
    build_receipt_payload,
    calculate_official_fee,
    ensure_receipt_metadata,
    generate_receipt_pdf_bytes,
    get_fee_schedule,
    verify_receipt_token,
)

router = APIRouter(tags=["Payments"])

VALID_MEMBERSHIP_AMOUNTS = {500, 1000, 1500, 2000, 2500, 5000, 10000}


def _validate_payment_amount(
    db: Session,
    purpose: str,
    amount: float,
    member: Member | None,
    event_registration_id: int | None,
    user: User,
) -> EventRegistration | None:
    if amount <= 0:
        raise HTTPException(400, "Payment amount must be greater than zero")

    registration = None
    norm_purpose = (purpose or "MEMBERSHIP").strip().upper()

    if event_registration_id:
        registration = db.scalar(
            select(EventRegistration).where(
                EventRegistration.id == event_registration_id,
                EventRegistration.user_id == user.id,
            )
        )
        if not registration:
            raise HTTPException(404, "Event registration not found")
        event = db.get(Event, registration.event_id)
        if not event or not event.fee_amount:
            raise HTTPException(409, "No payment is required for this event")
        if int(amount) != int(event.fee_amount):
            raise HTTPException(400, "Payment amount does not match event fee")
        return registration

    if norm_purpose in {"MEMBERSHIP", "RENEWAL", "APPLICATION"}:
        if not member:
            raise HTTPException(404, "Member profile not found")
        expected = calculate_official_fee(db, norm_purpose, getattr(member, "membership_type", "GENERAL"))
        allowed_amounts = set(VALID_MEMBERSHIP_AMOUNTS)
        if expected:
            allowed_amounts.add(int(expected))
        if int(amount) < 500 or int(amount) not in allowed_amounts:
            raise HTTPException(
                400,
                f"Payment amount (৳{amount}) does not match official PGCB fee schedule",
            )
    return None


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
        return {"status": "already_processed"}

    if gateway_status == "SUCCESS":
        # Double check with a synchronous server-to-server verification call
        if payment_service.verify_payment(provider_trx_id, expected_amount=float(transaction.amount)):
            transaction.status = PaymentStatus.PAID
            transaction.completed_at = datetime.utcnow()
            webhook_log.is_processed = True
            webhook_log.transaction_id = transaction.id
            db.commit()

            log_audit_action(
                db, request,
                action="PAYMENT_COMPLETED",
                entity="PAYMENT",
                entity_id=str(transaction.id),
                new_value={"provider": provider.value, "trx_id": provider_trx_id, "amount": transaction.amount}
            )

            try:
                from app.worker import send_receipt_task
                if send_receipt_task:
                    send_receipt_task.delay(str(transaction.id))
            except Exception:
                pass

            return {"status": "success"}

    return {"status": "ignored"}


# ==========================================================
# 2. Fee Schedule & Member Checkout Operations
# ==========================================================

@router.get("/public/membership-fees")
def public_membership_fees(db: Session = Depends(get_db)):
    schedule = get_fee_schedule(db)
    return {
        "currency": "BDT",
        "fees": schedule,
        "tiers": [
            {"code": "APPLICATION", "title_bn": "আবেদন ও নিবন্ধন ফি", "title_en": "Application Fee", "amount": schedule["APPLICATION"]},
            {"code": "GENERAL", "title_bn": "বার্ষিক সাধারণ সদস্যপদ ফি", "title_en": "Annual General Membership Fee", "amount": schedule["GENERAL"]},
            {"code": "RENEWAL", "title_bn": "বার্ষিক নবায়ন ফি", "title_en": "Annual Renewal Fee", "amount": schedule["RENEWAL"]},
            {"code": "LIFE", "title_bn": "আজীবন সদস্যপদ ফি", "title_en": "Life Membership Fee", "amount": schedule["LIFE"]},
        ],
    }


@router.get("/member/membership-fee")
def member_fee_calculation(user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    schedule = get_fee_schedule(db)
    mtype = (member.membership_type if member and member.membership_type else "GENERAL").upper()
    status = member.status if member else "PENDING"
    recommended_purpose = "RENEWAL" if status in {"ACTIVE", "EXPIRED"} else "MEMBERSHIP"
    amount = calculate_official_fee(db, recommended_purpose, mtype) or schedule["GENERAL"]
    return {
        "member_id": member.id if member else None,
        "membership_id": member.membership_id if member else None,
        "membership_type": mtype,
        "member_status": status,
        "recommended_purpose": recommended_purpose,
        "calculated_amount": amount,
        "currency": "BDT",
        "schedule": schedule,
    }


@router.post("/member/payments")
def create_payment(payload: PaymentCreate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    registration = _validate_payment_amount(
        db,
        payload.purpose,
        payload.amount,
        member,
        payload.event_registration_id,
        user,
    )
    if registration:
        registration.payment_status = 'PENDING'

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
@router.post("/member/payments/initiate")
@router.post("/payments/checkout")
def create_checkout_intent(payload: PaymentCreate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        provider = normalize_provider(payload.provider)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    member = db.scalar(select(Member).where(Member.user_id == user.id))
    registration = _validate_payment_amount(
        db,
        payload.purpose,
        payload.amount,
        member,
        payload.event_registration_id,
        user,
    )

    item = CorePaymentTransaction(
        user_id=user.id,
        member_id=member.id if member else None,
        event_registration_id=registration.id if registration else None,
        amount=int(payload.amount),
        currency=payload.currency.upper(),
        provider=provider,
        purpose=payload.purpose.upper(),
        status='PENDING'
    )
    db.add(item)
    db.flush()

    try:
        checkout = create_checkout(provider, item.id, float(item.amount), item.currency)
    except (RuntimeError, PermissionError) as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from exc

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
        'id': item.id,
        'payment_id': item.id,
        'provider': provider,
        'transaction_id': checkout.provider_transaction_id,
        'provider_transaction_id': checkout.provider_transaction_id,
        'checkout_url': checkout.checkout_url,
        'status': item.status,
        'amount': float(item.amount),
        'currency': item.currency
    }


@router.post("/member/payments/{payment_id}/confirm")
def confirm_payment_transaction(
    payment_id: int,
    provider_reference: str | None = None,
    request: Request = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    payment = db.get(CorePaymentTransaction, payment_id)
    if not payment:
        raise HTTPException(404, "Payment transaction not found")
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    is_owner = (payment.user_id == user.id) or (member and payment.member_id == member.id)
    if not is_owner and user.role == "MEMBER":
        raise HTTPException(403, "Not authorized to confirm this payment")

    ref_to_verify = (provider_reference or payment.transaction_ref or "").strip()
    if not ref_to_verify:
        raise HTTPException(400, "Missing provider transaction reference")

    gateway = get_payment_provider(payment.provider or "SSLCOMMERZ")
    if not gateway.verify_payment(ref_to_verify, expected_amount=float(payment.amount)):
        raise HTTPException(400, "Server-to-server gateway verification failed for transaction")

    payment.transaction_ref = ref_to_verify
    payment.status = "PAID"
    ensure_receipt_metadata(payment)
    activate_membership_from_payment(db, payment)
    db.commit()
    db.refresh(payment)
    return {
        "id": payment.id,
        "status": payment.status,
        "receipt_no": payment.receipt_no,
        "transaction_ref": payment.transaction_ref,
        "amount": float(payment.amount),
        "currency": payment.currency,
    }


@router.get("/member/payments")
def list_payments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    member_id = member.id if member else None

    stmt = (
        select(CorePaymentTransaction)
        .where(
            (CorePaymentTransaction.member_id == member_id) if member_id else (CorePaymentTransaction.user_id == user.id)
        )
        .order_by(CorePaymentTransaction.created_at.desc())
    )
    rows = db.scalars(stmt).all()

    return [
        {
            'id': p.id,
            'purpose': p.purpose or 'MEMBERSHIP',
            'amount': float(p.amount),
            'currency': p.currency,
            'provider': p.provider,
            'transaction_ref': p.transaction_ref,
            'receipt_no': p.receipt_no,
            'status': p.status,
            'created_at': p.created_at,
        }
        for p in rows
    ]


@router.get("/member/payments/{payment_id}/receipt")
def get_payment_receipt(payment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    payment = db.get(CorePaymentTransaction, payment_id)
    if not payment:
        raise HTTPException(404, "Payment transaction not found")
    is_owner = (payment.user_id == user.id) or (member and payment.member_id == member.id)
    if not is_owner and user.role == "MEMBER":
        raise HTTPException(403, "Not authorized to view this receipt")
    if payment.status not in {"PAID", "SUCCESS", "COMPLETED"}:
        raise HTTPException(409, "Receipt is only available for completed/paid transactions")
    if not payment.receipt_no:
        ensure_receipt_metadata(payment)
        db.commit()
        db.refresh(payment)
    return build_receipt_payload(db, payment)


@router.get("/member/payments/{payment_id}/receipt.pdf")
@router.get("/member/payments/{payment_id}/receipt/pdf")
def download_payment_receipt_pdf(payment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    receipt = get_payment_receipt(payment_id, user, db)
    pdf_bytes = generate_receipt_pdf_bytes(receipt)
    filename = f"{receipt['receipt_no']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/public/receipts/verify/{token_or_receipt_no}")
def verify_payment_receipt(token_or_receipt_no: str, db: Session = Depends(get_db)):
    valid_sig, receipt_no = verify_receipt_token(token_or_receipt_no)
    if not valid_sig or not receipt_no.startswith("PGCB-RCP-"):
        raise HTTPException(400, "Invalid receipt verification token")
    parts = receipt_no.split("-")
    if len(parts) < 4 or not parts[-1].isdigit():
        raise HTTPException(400, "Malformed receipt number")
    payment_id = int(parts[-1])
    payment = db.get(CorePaymentTransaction, payment_id)
    if not payment or payment.status not in {"PAID", "SUCCESS", "COMPLETED"}:
        raise HTTPException(404, "Verified payment receipt not found")
    data = build_receipt_payload(db, payment)
    return {
        "verified": True,
        "receipt_no": data["receipt_no"],
        "transaction_ref": data["transaction_ref"],
        "member_name_bn": data["member_name_bn"],
        "membership_id": data["membership_id"],
        "purpose": data["purpose"],
        "amount": data["amount"],
        "currency": data["currency"],
        "payment_method": data["payment_method"],
        "status": data["status"],
        "paid_at": data["paid_at"],
    }
