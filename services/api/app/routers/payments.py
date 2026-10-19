from __future__ import annotations

from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import Response
from sqlalchemy import select, or_, func
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
    confirm_event_registration_payment,
    ensure_receipt_metadata,
    generate_receipt_pdf_bytes,
    get_fee_schedule,
    resolve_plan_amount,
    verify_receipt_token,
)
from app.services.payment_service import transition_payment_status, validate_payment_transition

router = APIRouter(tags=["Payments"])

VALID_MEMBERSHIP_AMOUNTS = {500, 1000, 1500, 2000, 2500, 4000, 5000, 10000}


def _validate_payment_amount(
    db: Session,
    purpose: str,
    amount: float | None,
    member: Member | None,
    event_registration_id: int | None,
    user: User,
    membership_plan_id: str | None = None,
) -> tuple[EventRegistration | None, int]:
    registration = None
    norm_purpose = (purpose or "MEMBERSHIP").strip().upper()

    # 1. If membership_plan_id is provided, compute authoritative fee on the server
    if membership_plan_id:
        try:
            plan_amount = resolve_plan_amount(db, membership_plan_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if amount is not None and int(amount) != int(plan_amount):
            raise HTTPException(
                400,
                f"Client amount (৳{amount}) does not match server-calculated fee (৳{plan_amount}) for plan {membership_plan_id}",
            )
        amount = float(plan_amount)

    if amount is None or amount <= 0:
        raise HTTPException(422 if amount is not None and amount <= 0 else 400, "Payment amount must be greater than zero")

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
        return registration, int(amount)

    if norm_purpose in {"MEMBERSHIP", "MEMBERSHIP_FEE", "RENEWAL", "APPLICATION"} and not membership_plan_id:
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
    return None, int(amount)


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

    # 4. Look up CorePaymentTransaction first, then fallback to legacy PaymentTransaction
    core_tx = None
    if provider_trx_id:
        core_tx = db.scalar(
            select(CorePaymentTransaction).where(CorePaymentTransaction.transaction_ref == provider_trx_id)
        )
    if not core_tx and payload.get("payment_id") and str(payload["payment_id"]).isdigit():
        core_tx = db.get(CorePaymentTransaction, int(payload["payment_id"]))

    if core_tx:
        if core_tx.status in ("PAID", "SUCCESS"):
            if gateway_status in ("FAILED", "CANCELLED", "EXPIRED"):
                raise HTTPException(status_code=409, detail=f"Illegal payment state transition: {core_tx.status} -> {gateway_status}")
            confirm_event_registration_payment(db, core_tx)
            db.commit()
            return {"status": "already_processed", "idempotent_replay": True, "receipt_no": core_tx.receipt_no}

        if gateway_status == "SUCCESS":
            if payment_service.verify_payment(provider_trx_id, expected_amount=float(core_tx.amount)):
                core_tx.provider_transaction_id = provider_trx_id
                transition_payment_status(core_tx, "PAID")
                ensure_receipt_metadata(core_tx)
                confirm_event_registration_payment(db, core_tx)
                activate_membership_from_payment(db, core_tx)
                webhook_log.is_processed = True
                db.commit()
                log_audit_action(
                    db, request,
                    action="PAYMENT_COMPLETED",
                    entity="PAYMENT",
                    entity_id=str(core_tx.id),
                    new_value={"provider": provider.value, "trx_id": provider_trx_id, "amount": float(core_tx.amount)},
                )
                return {"status": "success", "receipt_no": core_tx.receipt_no}
            else:
                transition_payment_status(core_tx, "FAILED")
                db.commit()
                return {"status": "verification_failed"}
        elif gateway_status in ("FAILED", "CANCELLED", "EXPIRED"):
            transition_payment_status(core_tx, gateway_status)
            db.commit()
            return {"status": gateway_status.lower()}

    # Fallback for legacy gateway_payment_transactions table
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

    if transaction.status in (PaymentStatus.PAID, "PAID", "SUCCESS"):
        confirm_event_registration_payment(db, transaction)
        db.commit()
        return {"status": "already_processed"}

    if gateway_status == "SUCCESS":
        if payment_service.verify_payment(provider_trx_id, expected_amount=float(transaction.amount)):
            transaction.status = PaymentStatus.PAID
            transaction.completed_at = datetime.utcnow()
            confirm_event_registration_payment(db, transaction)
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
            {"code": "ANNUAL_STANDARD", "title_bn": "বার্ষিক সাধারণ সদস্যপদ ফি", "title_en": "Annual Standard Membership Fee", "amount": schedule["ANNUAL_STANDARD"]},
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
def create_payment(
    payload: PaymentCreate,
    request: Request,
    x_idempotency_key: str | None = Header(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if any(val is not None for val in (payload.status, payload.payment_status, payload.membership_status)):
        raise HTTPException(403, 'Browser cannot directly modify payment_status or membership_status')
    idem_key = (payload.idempotency_key or x_idempotency_key or "").strip() or None
    if idem_key:
        existing = db.scalar(select(CorePaymentTransaction).where(CorePaymentTransaction.idempotency_key == idem_key))
        if existing:
            return {
                'id': existing.id,
                'status': existing.status,
                'amount': existing.amount,
                'currency': existing.currency,
                'provider': existing.provider,
                'transaction_ref': existing.transaction_ref,
                'membership_plan_id': existing.membership_plan_id,
                'idempotent_replay': True,
                'message': 'Existing idempotent payment returned.'
            }

    member = db.scalar(select(Member).where(Member.user_id == user.id))
    registration, validated_amount = _validate_payment_amount(
        db,
        payload.purpose,
        payload.amount,
        member,
        payload.event_registration_id,
        user,
        membership_plan_id=payload.membership_plan_id,
    )
    if registration:
        registration.payment_status = 'PENDING'

    item = CorePaymentTransaction(
        user_id=user.id,
        member_id=member.id if member else None,
        event_registration_id=payload.event_registration_id,
        membership_plan_id=payload.membership_plan_id.upper() if payload.membership_plan_id else None,
        idempotency_key=idem_key,
        amount=int(validated_amount),
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
        new_value={"amount": item.amount, "currency": item.currency, "provider": str(item.provider), "plan": item.membership_plan_id}
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
        'membership_plan_id': item.membership_plan_id,
        'message': 'Payment intent created. Connect a configured gateway or submit transaction reference for verification.'
    }


@router.post("/member/payments/checkout")
@router.post("/member/payments/initiate")
@router.post("/payments/checkout")
def create_checkout_intent(
    payload: PaymentCreate,
    request: Request,
    x_idempotency_key: str | None = Header(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if any(val is not None for val in (payload.status, payload.payment_status, payload.membership_status)):
        raise HTTPException(403, 'Browser cannot directly modify payment_status or membership_status')
    try:
        provider = normalize_provider(payload.provider)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    idem_key = (payload.idempotency_key or x_idempotency_key or "").strip() or None
    if idem_key:
        existing = db.scalar(select(CorePaymentTransaction).where(CorePaymentTransaction.idempotency_key == idem_key))
        if existing:
            return {
                'id': existing.id,
                'payment_id': existing.id,
                'provider': existing.provider,
                'transaction_id': existing.transaction_ref,
                'provider_transaction_id': existing.provider_transaction_id or existing.transaction_ref,
                'checkout_url': f"/portal?payment_id={existing.id}",
                'status': existing.status,
                'amount': float(existing.amount),
                'currency': existing.currency,
                'membership_plan_id': existing.membership_plan_id,
                'idempotent_replay': True,
            }

    member = db.scalar(select(Member).where(Member.user_id == user.id))
    registration, validated_amount = _validate_payment_amount(
        db,
        payload.purpose,
        payload.amount,
        member,
        payload.event_registration_id,
        user,
        membership_plan_id=payload.membership_plan_id,
    )
    if registration:
        registration.payment_status = 'PENDING'

    item = CorePaymentTransaction(
        user_id=user.id,
        member_id=member.id if member else None,
        event_registration_id=registration.id if registration else None,
        membership_plan_id=payload.membership_plan_id.upper() if payload.membership_plan_id else None,
        idempotency_key=idem_key,
        amount=int(validated_amount),
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
        new_value={"provider": provider, "trx_id": checkout.provider_transaction_id, "amount": float(item.amount), "plan": item.membership_plan_id}
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
        'currency': item.currency,
        'membership_plan_id': item.membership_plan_id,
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

    # Idempotency check: if already PAID/SUCCESS, return existing result without re-processing
    if payment.status in ("PAID", "SUCCESS"):
        confirm_event_registration_payment(db, payment)
        db.commit()
        return {
            "id": payment.id,
            "status": payment.status,
            "receipt_no": payment.receipt_no,
            "transaction_ref": payment.transaction_ref,
            "provider_transaction_id": payment.provider_transaction_id,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "idempotent_replay": True,
        }

    if not validate_payment_transition(payment.status, "PAID"):
        raise HTTPException(409, f"Illegal payment state transition: {payment.status} -> PAID")

    # Check if another transaction already claimed this provider_transaction_id
    dup_trx = db.scalar(
        select(CorePaymentTransaction).where(
            CorePaymentTransaction.provider_transaction_id_col == ref_to_verify,
            CorePaymentTransaction.id != payment.id,
        )
    )
    if dup_trx:
        raise HTTPException(409, "provider_transaction_id already processed for another transaction")

    gateway = get_payment_provider(payment.provider or "SSLCOMMERZ")
    if not gateway.verify_payment(ref_to_verify, expected_amount=float(payment.amount)):
        raise HTTPException(400, "Server-to-server gateway verification failed for transaction")

    payment.transaction_ref = ref_to_verify
    payment.provider_transaction_id = ref_to_verify
    transition_payment_status(payment, "PAID")
    ensure_receipt_metadata(payment)
    confirm_event_registration_payment(db, payment)
    activate_membership_from_payment(db, payment)
    db.commit()
    db.refresh(payment)
    return {
        "id": payment.id,
        "status": payment.status,
        "receipt_no": payment.receipt_no,
        "transaction_ref": payment.transaction_ref,
        "provider_transaction_id": payment.provider_transaction_id,
        "amount": float(payment.amount),
        "currency": payment.currency,
    }


@router.post("/payments/callback/{provider}")
@router.post("/member/payments/callback/{provider}")
def callback_payment_transaction(
    provider: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Production Payment Callback / Server Verification Endpoint:
    Provider -> Transaction -> Gateway -> Callback -> Server verification ->
    Idempotency -> State Machine -> SUCCESS -> Membership activation -> Receipt.
    """
    tx_lookup = payload.get("transaction_id") or payload.get("payment_id") or payload.get("tran_id")
    if not tx_lookup:
        raise HTTPException(400, "Missing transaction_id in callback payload")

    payment = None
    if str(tx_lookup).isdigit():
        payment = db.get(CorePaymentTransaction, int(tx_lookup))
    if not payment:
        payment = db.scalar(select(CorePaymentTransaction).where(CorePaymentTransaction.transaction_ref == str(tx_lookup)))
    if not payment:
        raise HTTPException(404, "Payment transaction not found")

    prov_trx_id = (
        payload.get("provider_transaction_id")
        or payload.get("trxID")
        or payload.get("trx_id")
        or payload.get("val_id")
        or payload.get("issuer_trx_id")
        or payment.transaction_ref
        or ""
    ).strip()
    incoming_status = str(payload.get("status") or "SUCCESS").strip().upper()
    target_status = "PAID" if incoming_status in ("SUCCESS", "PAID", "COMPLETED", "VALID") else incoming_status

    # 1. Cross-transaction provider_transaction_id uniqueness check
    if prov_trx_id:
        dup_trx = db.scalar(
            select(CorePaymentTransaction).where(
                CorePaymentTransaction.provider_transaction_id_col == prov_trx_id,
                CorePaymentTransaction.id != payment.id,
            )
        )
        if dup_trx:
            raise HTTPException(409, "provider_transaction_id already processed for another transaction")

    # 2. Idempotency & State Machine guard for already completed payments
    if payment.status in ("PAID", "SUCCESS"):
        if target_status in ("FAILED", "CANCELLED", "EXPIRED"):
            raise HTTPException(409, f"Illegal payment state transition: {payment.status} -> {target_status}")
        confirm_event_registration_payment(db, payment)
        db.commit()
        return {
            "id": payment.id,
            "payment_id": payment.id,
            "transaction_id": payment.transaction_ref,
            "provider_transaction_id": payment.provider_transaction_id,
            "status": payment.status,
            "receipt_no": payment.receipt_no,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "idempotent_replay": True,
        }

    # 3. Validate state transition
    if not validate_payment_transition(payment.status, target_status):
        raise HTTPException(409, f"Illegal payment state transition: {payment.status} -> {target_status}")

    if target_status in ("FAILED", "CANCELLED", "EXPIRED"):
        transition_payment_status(payment, target_status)
        db.commit()
        db.refresh(payment)
        return {
            "id": payment.id,
            "payment_id": payment.id,
            "transaction_id": payment.transaction_ref,
            "status": payment.status,
        }

    # 4. Server-to-server gateway verification & amount check
    if not prov_trx_id:
        transition_payment_status(payment, "FAILED")
        db.commit()
        raise HTTPException(400, "Missing provider_transaction_id for verification")

    gateway = get_payment_provider(provider or payment.provider or "TEST")
    if not gateway.verify_payment(prov_trx_id, expected_amount=float(payment.amount)):
        transition_payment_status(payment, "FAILED")
        db.commit()
        raise HTTPException(400, "Server-to-server gateway verification failed for transaction")

    payment.provider_transaction_id = prov_trx_id
    transition_payment_status(payment, "PAID")
    ensure_receipt_metadata(payment)
    confirm_event_registration_payment(db, payment)
    activate_membership_from_payment(db, payment)
    db.commit()
    db.refresh(payment)
    return {
        "id": payment.id,
        "payment_id": payment.id,
        "transaction_id": payment.transaction_ref,
        "provider_transaction_id": payment.provider_transaction_id,
        "status": payment.status,
        "receipt_no": payment.receipt_no,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "idempotent_replay": False,
    }


PAYMENT_PURPOSE_EN_MAP = {
    'MEMBERSHIP': 'Membership Fee',
    'MEMBERSHIP_FEE': 'Membership Fee',
    'RENEWAL': 'Membership Renewal Fee',
    'MEMBERSHIP_RENEWAL': 'Membership Renewal Fee',
    'APPLICATION': 'Membership Application Fee',
    'EVENT': 'Event Registration Fee',
    'DONATION': 'Welfare Contribution',
}

PAYMENT_PURPOSE_BN_MAP = {
    'MEMBERSHIP': 'সদস্যপদ ফি',
    'MEMBERSHIP_FEE': 'সদস্যপদ ফি',
    'RENEWAL': 'সদস্যপদ নবায়ন ফি',
    'MEMBERSHIP_RENEWAL': 'সদস্যপদ নবায়ন ফি',
    'APPLICATION': 'সদস্যপদ আবেদন ফি',
    'EVENT': 'ইভেন্ট নিবন্ধন ফি',
    'DONATION': 'কল্যাণ তহবিল অনুদান',
}

PAYMENT_STATUS_BN_MAP = {
    'INITIATED': 'শুরু করা হয়েছে',
    'PENDING': 'অপেক্ষমান (Pending)',
    'PROCESSING': 'প্রক্রিয়াধীন',
    'PAID': 'পরিশোধিত (Paid)',
    'SUCCESS': 'পরিশোধিত (Success)',
    'FAILED': 'ব্যর্থ (Failed)',
    'CANCELLED': 'বাতিল (Cancelled)',
    'EXPIRED': 'মেয়াদোত্তীর্ণ (Expired)',
    'REFUNDED': 'রিফান্ডকৃত (Refunded)',
    'PARTIALLY_REFUNDED': 'আংশিক রিফান্ডকৃত',
}

FINANCE_ADMIN_ROLES = {
    'SUPER_ADMIN',
    'CENTRAL_ADMIN',
    'FINANCE_OFFICER',
    'FINANCE_ADMIN',
}


def _format_payment_item(p: CorePaymentTransaction) -> dict[str, Any]:
    purpose_key = (p.purpose or 'MEMBERSHIP').upper()
    is_paid = p.status in ('PAID', 'SUCCESS', 'COMPLETED')
    created_dt = p.created_at or datetime.utcnow()
    ref = p.transaction_ref or f"PGCB-PAY-{created_dt.year}-{p.id:06d}"
    completed_dt = p.completed_at or p.updated_at if is_paid else None

    return {
        'id': p.id,
        'reference': ref,
        'transaction_ref': ref,
        'member_id': p.member_id,
        'user_id': p.user_id,
        'date': created_dt.strftime('%Y-%m-%d'),
        'purpose': purpose_key,
        'purpose_label': PAYMENT_PURPOSE_EN_MAP.get(purpose_key, 'Membership Fee'),
        'purpose_label_en': PAYMENT_PURPOSE_EN_MAP.get(purpose_key, 'Membership Fee'),
        'purpose_label_bn': PAYMENT_PURPOSE_BN_MAP.get(purpose_key, 'সদস্যপদ ফি'),
        'membership_plan_id': p.membership_plan_id,
        'amount': float(p.amount),
        'amount_formatted': f"৳{int(p.amount):,}",
        'currency': p.currency or 'BDT',
        'provider': p.provider,
        'gateway': p.provider,
        'provider_tran_id': p.provider_transaction_id or p.transaction_ref,
        'gateway_transaction_id': p.provider_transaction_id or p.transaction_ref,
        'receipt_no': p.receipt_no,
        'status': 'PAID' if is_paid else p.status,
        'status_label_en': 'PAID' if is_paid else p.status,
        'status_label_bn': PAYMENT_STATUS_BN_MAP.get(p.status, p.status),
        'receipt_available': is_paid,
        'has_receipt': is_paid,
        'receipt_url': f"/api/v1/member/payments/{p.id}/receipt" if is_paid else None,
        'receipt_pdf_url': f"/api/v1/member/payments/{p.id}/receipt.pdf" if is_paid else None,
        'created_at': created_dt.isoformat(),
        'paid_at': completed_dt.isoformat() if completed_dt else None,
    }


def _compute_payment_summary(user: User, db: Session, status_filter: str | None = None) -> dict[str, Any]:
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    member_id = member.id if member else None

    stmt = (
        select(CorePaymentTransaction)
        .where(
            (CorePaymentTransaction.member_id == member_id) if member_id else (CorePaymentTransaction.user_id == user.id)
        )
        .order_by(CorePaymentTransaction.created_at.desc())
    )
    all_rows = db.scalars(stmt).all()

    total_paid = sum(float(p.amount) for p in all_rows if p.status in ('PAID', 'SUCCESS', 'COMPLETED'))
    successful_count = sum(1 for p in all_rows if p.status in ('PAID', 'SUCCESS', 'COMPLETED'))
    pending_count = sum(1 for p in all_rows if p.status in ('PENDING', 'INITIATED', 'PROCESSING'))
    failed_count = sum(1 for p in all_rows if p.status in ('FAILED', 'CANCELLED', 'EXPIRED'))
    refunded_count = sum(1 for p in all_rows if p.status in ('REFUNDED', 'PARTIALLY_REFUNDED'))

    filtered_rows = all_rows
    if status_filter:
        s_upper = status_filter.strip().upper()
        if s_upper in ('PAID', 'SUCCESS', 'SUCCESSFUL'):
            filtered_rows = [p for p in all_rows if p.status in ('PAID', 'SUCCESS', 'COMPLETED')]
        elif s_upper == 'PENDING':
            filtered_rows = [p for p in all_rows if p.status in ('PENDING', 'INITIATED', 'PROCESSING')]
        elif s_upper == 'FAILED':
            filtered_rows = [p for p in all_rows if p.status in ('FAILED', 'CANCELLED', 'EXPIRED')]
        elif s_upper == 'REFUNDED':
            filtered_rows = [p for p in all_rows if p.status in ('REFUNDED', 'PARTIALLY_REFUNDED')]
        else:
            filtered_rows = [p for p in all_rows if p.status == s_upper]

    transactions = [_format_payment_item(p) for p in filtered_rows]

    return {
        "total_paid": total_paid,
        "total_paid_formatted": f"৳{int(total_paid):,}",
        "successful_count": successful_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "refunded_count": refunded_count,
        "transactions": transactions,
    }


def _get_payment_items_list(user: User, db: Session, status_filter: str | None = None) -> list[dict[str, Any]]:
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
    if status_filter:
        s_upper = status_filter.strip().upper()
        if s_upper in ('PAID', 'SUCCESS', 'SUCCESSFUL'):
            rows = [p for p in rows if p.status in ('PAID', 'SUCCESS', 'COMPLETED')]
        elif s_upper == 'PENDING':
            rows = [p for p in rows if p.status in ('PENDING', 'INITIATED', 'PROCESSING')]
        elif s_upper == 'FAILED':
            rows = [p for p in rows if p.status in ('FAILED', 'CANCELLED', 'EXPIRED')]
        elif s_upper == 'REFUNDED':
            rows = [p for p in rows if p.status in ('REFUNDED', 'PARTIALLY_REFUNDED')]
        else:
            rows = [p for p in rows if p.status == s_upper]

    return [_format_payment_item(p) for p in rows]


@router.get("/member/payments/summary")
def member_payments_summary(
    status: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return _compute_payment_summary(user, db, status_filter=status)


@router.get("/member/payments")
def list_payments(
    summary: bool = False,
    status: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if summary:
        return _compute_payment_summary(user, db, status_filter=status)
    return _get_payment_items_list(user, db, status_filter=status)


@router.get("/member/payments/{payment_id}")
def get_payment_detail(
    payment_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    payment = None
    if str(payment_id).isdigit():
        payment = db.get(CorePaymentTransaction, int(payment_id))
    if not payment:
        payment = db.scalar(
            select(CorePaymentTransaction).where(CorePaymentTransaction.transaction_ref == str(payment_id))
        )
    if not payment:
        raise HTTPException(404, "Payment transaction not found")

    member = db.scalar(select(Member).where(Member.user_id == user.id))
    is_owner = (payment.user_id == user.id) or (member and payment.member_id == member.id)
    is_admin = user.role in FINANCE_ADMIN_ROLES or user.role in ("SUPER_ADMIN", "CENTRAL_ADMIN")
    if not is_owner and not is_admin:
        raise HTTPException(403, "Not authorized to access this payment transaction")

    item = _format_payment_item(payment)
    if payment.status in ("PAID", "SUCCESS", "COMPLETED"):
        item["receipt"] = build_receipt_payload(db, payment)
    return item


@router.get("/member/payments/{payment_id}/receipt")
def get_payment_receipt(payment_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    payment = None
    if str(payment_id).isdigit():
        payment = db.get(CorePaymentTransaction, int(payment_id))
    if not payment:
        payment = db.scalar(select(CorePaymentTransaction).where(CorePaymentTransaction.transaction_ref == str(payment_id)))
    if not payment:
        raise HTTPException(404, "Payment transaction not found")
    is_owner = (payment.user_id == user.id) or (member and payment.member_id == member.id)
    is_admin = user.role in FINANCE_ADMIN_ROLES or user.role in ("SUPER_ADMIN", "CENTRAL_ADMIN")
    if not is_owner and not is_admin:
        raise HTTPException(403, "Not authorized to view this receipt")
    if payment.status not in {"PAID", "SUCCESS", "COMPLETED"}:
        raise HTTPException(409, "Receipt is only available for completed/paid transactions")
    if not payment.receipt_no:
        ensure_receipt_metadata(payment)
        db.commit()
        db.refresh(payment)
    return build_receipt_payload(db, payment)


@router.get("/member/payments/{payment_id}/receipt.pdf", operation_id="download_payment_receipt_pdf_dot")
@router.get("/member/payments/{payment_id}/receipt/pdf")
@router.get("/payments/transactions/{payment_id}/receipt.pdf", operation_id="download_transaction_receipt_pdf")
def download_payment_receipt_pdf(payment_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    receipt = get_payment_receipt(payment_id, user, db)
    pdf_bytes = generate_receipt_pdf_bytes(receipt)
    filename = f"{receipt['receipt_no']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/public/verify/payment/{reference}")
@router.get("/verify/payment/{reference}")
@router.get("/public/receipts/verify/{reference}")
def verify_payment_public(reference: str, db: Session = Depends(get_db)):
    ref = reference.strip()
    payment = None

    # 1. Try HMAC signature token
    if "." in ref:
        valid_sig, receipt_no = verify_receipt_token(ref)
        if valid_sig and receipt_no.startswith("PGCB-RCP-"):
            parts = receipt_no.split("-")
            if len(parts) >= 4 and parts[-1].isdigit():
                payment = db.get(CorePaymentTransaction, int(parts[-1]))

    # 2. Try receipt_no match in provider_payload
    if not payment:
        try:
            payment = db.scalar(
                select(CorePaymentTransaction).where(
                    or_(
                        CorePaymentTransaction.provider_payload["receipt_no"].as_string() == ref,
                        CorePaymentTransaction.provider_payload["receipt_token"].as_string() == ref,
                    )
                )
            )
        except Exception:
            pass

    # 3. Try transaction_ref or provider_transaction_id
    if not payment:
        payment = db.scalar(
            select(CorePaymentTransaction).where(
                or_(
                    CorePaymentTransaction.transaction_ref == ref,
                    CorePaymentTransaction.provider_transaction_id_col == ref,
                )
            )
        )

    # 4. Try receipt number format PGCB-RCP-YYYY-NNNNNN or PGCB-PAY-YYYY-NNNNNN
    if not payment and (ref.startswith("PGCB-RCP-") or ref.startswith("PGCB-REC-") or ref.startswith("PGCB-PAY-")):
        parts = ref.split("-")
        if len(parts) >= 4 and parts[-1].isdigit():
            payment = db.get(CorePaymentTransaction, int(parts[-1]))

    # 5. Try plain numeric ID
    if not payment and ref.isdigit():
        payment = db.get(CorePaymentTransaction, int(ref))

    if not payment:
        raise HTTPException(404, "Verified payment record not found")

    is_paid = payment.status in {"PAID", "SUCCESS", "COMPLETED"}
    if not is_paid:
        member = db.get(Member, payment.member_id) if payment.member_id else None
        user = db.get(User, payment.user_id) if payment.user_id else (db.get(User, member.user_id) if member and member.user_id else None)
        return {
            "verified": False,
            "is_valid": False,
            "status": payment.status,
            "transaction_ref": payment.transaction_ref,
            "receipt_no": None,
            "member_name": (user.name_en if user else None) or "Member",
            "member_name_bn": user.name_bn if user else None,
            "membership_id": member.membership_id if member else None,
            "amount": float(payment.amount),
            "amount_formatted": f"৳{int(payment.amount):,}",
            "currency": payment.currency or "BDT",
            "message": f"Payment is in {payment.status} state, not verified as completed.",
        }

    data = build_receipt_payload(db, payment)
    return {
        "verified": True,
        "is_valid": True,
        "payment_id": payment.id,
        "receipt_no": data["receipt_no"],
        "transaction_ref": data["transaction_ref"],
        "member_name": data["member_name_en"],
        "member_name_bn": data["member_name_bn"],
        "membership_id": data["membership_id"],
        "purpose": data["purpose"],
        "purpose_title_en": data["purpose_label"],
        "purpose_title_bn": PAYMENT_PURPOSE_BN_MAP.get((data["purpose"] or '').upper(), "সদস্যপদ ফি"),
        "amount": data["amount"],
        "amount_formatted": data["amount_formatted"],
        "currency": data["currency"],
        "payment_method": data["payment_method"],
        "provider": data["payment_method"],
        "provider_tran_id": payment.provider_transaction_id or payment.transaction_ref,
        "status": "PAID",
        "paid_at": data["paid_at"],
        "payment_date": data["paid_at"],
        "verification_url": data["verification_url"],
        "verification_qr_data": data["verification_url"],
        "download_pdf_url": f"/api/v1/member/payments/{payment.id}/receipt.pdf",
    }


# ==========================================================
# 3. Admin Payment Management & Reconciliation Operations
# ==========================================================

@router.get("/admin/payments")
def list_admin_payments(
    status: str | None = None,
    member_id: int | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    admin: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if admin.role not in FINANCE_ADMIN_ROLES and admin.role not in ("SUPER_ADMIN", "CENTRAL_ADMIN"):
        raise HTTPException(403, "Admin privileges required to view payment console")

    stmt = select(CorePaymentTransaction).order_by(CorePaymentTransaction.created_at.desc())
    if member_id:
        stmt = stmt.where(CorePaymentTransaction.member_id == member_id)
    if status:
        s_upper = status.strip().upper()
        if s_upper in ('PAID', 'SUCCESS', 'SUCCESSFUL'):
            stmt = stmt.where(CorePaymentTransaction.status.in_(['PAID', 'SUCCESS', 'COMPLETED']))
        elif s_upper == 'PENDING':
            stmt = stmt.where(CorePaymentTransaction.status.in_(['PENDING', 'INITIATED', 'PROCESSING']))
        elif s_upper == 'FAILED':
            stmt = stmt.where(CorePaymentTransaction.status.in_(['FAILED', 'CANCELLED', 'EXPIRED']))
        elif s_upper == 'REFUNDED':
            stmt = stmt.where(CorePaymentTransaction.status.in_(['REFUNDED', 'PARTIALLY_REFUNDED']))
        else:
            stmt = stmt.where(CorePaymentTransaction.status == s_upper)

    all_rows = db.scalars(stmt).all()

    total_collected = sum(float(p.amount) for p in all_rows if p.status in ('PAID', 'SUCCESS', 'COMPLETED'))
    successful_count = sum(1 for p in all_rows if p.status in ('PAID', 'SUCCESS', 'COMPLETED'))
    pending_count = sum(1 for p in all_rows if p.status in ('PENDING', 'INITIATED', 'PROCESSING'))
    failed_count = sum(1 for p in all_rows if p.status in ('FAILED', 'CANCELLED', 'EXPIRED'))
    refunded_count = sum(1 for p in all_rows if p.status in ('REFUNDED', 'PARTIALLY_REFUNDED'))

    paginated_rows = all_rows[offset : offset + limit]
    transactions = [_format_payment_item(p) for p in paginated_rows]

    return {
        "total_collected": total_collected,
        "total_collected_formatted": f"৳{int(total_collected):,}",
        "successful_count": successful_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "refunded_count": refunded_count,
        "total_count": len(all_rows),
        "transactions": transactions,
    }


@router.post("/admin/payments/{payment_id}/reconcile")
def admin_reconcile_payment(
    payment_id: int,
    payload: dict,
    request: Request,
    admin: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if admin.role not in FINANCE_ADMIN_ROLES and admin.role not in ("SUPER_ADMIN", "CENTRAL_ADMIN"):
        raise HTTPException(403, "Admin privileges required to reconcile payments")

    payment = db.get(CorePaymentTransaction, payment_id)
    if not payment:
        raise HTTPException(404, "Payment transaction not found")

    if payment.status in ("PAID", "SUCCESS", "COMPLETED"):
        return {
            "ok": True,
            "status": "already_reconciled",
            "payment": _format_payment_item(payment),
            "message": "Payment is already marked as PAID.",
        }

    if not validate_payment_transition(payment.status, "PAID"):
        raise HTTPException(409, f"Illegal state transition from {payment.status} to PAID")

    prov_ref = (payload.get("provider_transaction_id") or payload.get("bank_reference") or f"MANUAL-REC-{admin.id}-{payment.id}").strip()
    existing_prov = db.scalar(
        select(CorePaymentTransaction).where(
            CorePaymentTransaction.provider_transaction_id == prov_ref,
            CorePaymentTransaction.id != payment.id,
        )
    )
    if existing_prov:
        prov_ref = f"{prov_ref}-{payment.id}"

    note = (payload.get("note") or payload.get("reconciliation_note") or "Manually reconciled by finance admin").strip()

    payment.provider_transaction_id = prov_ref
    if not payment.transaction_ref:
        payment.transaction_ref = prov_ref
    payment.provider = payload.get("method") or payment.provider or "MANUAL"

    transition_payment_status(payment, "PAID")
    ensure_receipt_metadata(payment)
    confirm_event_registration_payment(db, payment)
    activate_membership_from_payment(db, payment)

    payload_data = dict(payment.provider_payload or {})
    payload_data["reconciled_by"] = admin.id
    payload_data["reconciliation_note"] = note
    payload_data["reconciled_at"] = datetime.utcnow().isoformat()
    payment.provider_payload = payload_data

    log_audit_action(
        db, request,
        action="PAYMENT_RECONCILED",
        entity="PAYMENT",
        entity_id=str(payment.id),
        user=admin,
        new_value={"trx_id": prov_ref, "amount": float(payment.amount), "note": note},
    )
    db.commit()
    db.refresh(payment)

    return {
        "ok": True,
        "payment": _format_payment_item(payment),
        "message": "Payment successfully reconciled and membership updated.",
    }


@router.post("/admin/payments/{payment_id}/refund")
def admin_refund_payment(
    payment_id: int,
    payload: dict,
    request: Request,
    admin: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if admin.role not in FINANCE_ADMIN_ROLES and admin.role not in ("SUPER_ADMIN", "CENTRAL_ADMIN"):
        raise HTTPException(403, "Admin privileges required to refund payments")

    payment = db.get(CorePaymentTransaction, payment_id)
    if not payment:
        raise HTTPException(404, "Payment transaction not found")

    if payment.status not in ("PAID", "SUCCESS", "COMPLETED"):
        raise HTTPException(400, f"Cannot refund a payment in {payment.status} status. Only PAID transactions can be refunded.")

    reason = (payload.get("reason") or "Administrative refund request").strip()
    refund_ref = (payload.get("refund_ref") or f"REFUND-{payment.id}-{int(datetime.utcnow().timestamp())}").strip()
    refund_amount = payload.get("amount")

    target_status = "PARTIALLY_REFUNDED" if refund_amount and float(refund_amount) < float(payment.amount) else "REFUNDED"
    transition_payment_status(payment, target_status)

    payload_data = dict(payment.provider_payload or {})
    payload_data["refund_ref"] = refund_ref
    payload_data["refund_reason"] = reason
    payload_data["refunded_by"] = admin.id
    payload_data["refunded_at"] = datetime.utcnow().isoformat()
    payload_data["refund_amount"] = float(refund_amount) if refund_amount else float(payment.amount)
    payment.provider_payload = payload_data

    log_audit_action(
        db, request,
        action="PAYMENT_REFUNDED",
        entity="PAYMENT",
        entity_id=str(payment.id),
        user=admin,
        new_value={"refund_ref": refund_ref, "reason": reason, "status": target_status},
    )
    db.commit()
    db.refresh(payment)

    return {
        "ok": True,
        "status": target_status,
        "payment": _format_payment_item(payment),
        "message": f"Payment {payment.id} has been marked as {target_status}.",
    }


@router.post("/payments/sandbox/simulate")
def simulate_sandbox_payment_webhook(
    payload: dict,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Simulate a complete payment gateway webhook in sandbox/development mode:
    Development -> Payment Sandbox -> Successful payment -> Webhook simulation -> Membership activation.
    """
    if settings.payment_mode.lower() != "sandbox" and settings.is_production_like:
        raise HTTPException(403, "Sandbox payment simulation is disabled when PAYMENT_MODE is not sandbox")

    payment_id = payload.get("payment_id")
    transaction_ref = payload.get("transaction_ref")
    core_tx = None
    if payment_id and str(payment_id).isdigit():
        core_tx = db.get(CorePaymentTransaction, int(payment_id))
    elif transaction_ref:
        core_tx = db.scalar(
            select(CorePaymentTransaction).where(CorePaymentTransaction.transaction_ref == str(transaction_ref))
        )
    if not core_tx:
        raise HTTPException(404, "Payment transaction not found")

    if user.role == "MEMBER" and core_tx.user_id != user.id:
        raise HTTPException(403, "Not authorized to access or simulate another member's payment")

    if payload.get("amount") is not None and float(payload.get("amount")) != float(core_tx.amount):
        raise HTTPException(400, "Tampered payment amount does not match server record")

    if core_tx.status in ("PAID", "SUCCESS"):
        confirm_event_registration_payment(db, core_tx)
        db.commit()
        return {
            "status": "already_processed",
            "idempotent_replay": True,
            "payment_id": core_tx.id,
            "receipt_no": core_tx.receipt_no,
        }

    sim_outcome = str(payload.get("outcome") or payload.get("status") or "SUCCESS").strip().upper()
    if sim_outcome in ("FAILED", "CANCELLED", "EXPIRED"):
        transition_payment_status(core_tx, sim_outcome)
        db.commit()
        db.refresh(core_tx)
        member = db.get(Member, core_tx.member_id) if core_tx.member_id else None
        return {
            "status": "failed",
            "payment_mode": settings.payment_mode,
            "payment_id": core_tx.id,
            "payment_status": core_tx.status,
            "member_status": member.status if member else None,
            "membership_id": member.membership_id if member else None,
        }

    sim_trx_id = payload.get("provider_transaction_id") or f"SANDBOX-{core_tx.provider or 'BKASH'}-{core_tx.id}"
    core_tx.provider_transaction_id = sim_trx_id
    if not core_tx.transaction_ref:
        core_tx.transaction_ref = sim_trx_id
    transition_payment_status(core_tx, "PAID")
    ensure_receipt_metadata(core_tx)
    confirm_event_registration_payment(db, core_tx)
    activate_membership_from_payment(db, core_tx)

    webhook_log = PaymentWebhook(
        provider=PaymentProviderType.BKASH,
        payload={"sandbox_simulation": True, "payment_id": core_tx.id, "trxID": sim_trx_id},
        is_processed=True,
    )
    db.add(webhook_log)

    from app.models import Membership, Payment as CanonicalPayment
    if not db.scalar(
        select(CanonicalPayment).where(
            or_(
                CanonicalPayment.transaction_id == sim_trx_id,
                CanonicalPayment.receipt_no == core_tx.receipt_no,
            )
        )
    ):
        db.add(
            CanonicalPayment(
                user_id=core_tx.user_id,
                member_id=core_tx.member_id,
                transaction_id=sim_trx_id,
                receipt_no=core_tx.receipt_no,
                provider=core_tx.provider or "BKASH",
                purpose=core_tx.purpose or "MEMBERSHIP",
                amount=int(core_tx.amount),
                currency=core_tx.currency or "BDT",
                status="PAID",
                paid_at=datetime.utcnow(),
            )
        )
    member = db.get(Member, core_tx.member_id) if core_tx.member_id else None
    if member and member.membership_id:
        if not db.scalar(select(Membership).where(Membership.membership_id == member.membership_id)):
            db.add(
                Membership(
                    member_id=member.id,
                    membership_id=member.membership_id,
                    membership_type=member.membership_type or "GENERAL",
                    status=member.status or "ACTIVE",
                    issue_date=member.issue_date or datetime.utcnow(),
                    validity_date=member.validity_date,
                )
            )

    db.commit()
    db.refresh(core_tx)
    log_audit_action(
        db,
        request,
        action="SANDBOX_PAYMENT_SIMULATED",
        entity="PAYMENT",
        entity_id=str(core_tx.id),
        user=user,
        new_value={"trx_id": sim_trx_id, "amount": float(core_tx.amount), "receipt_no": core_tx.receipt_no},
    )
    return {
        "status": "success",
        "payment_mode": settings.payment_mode,
        "payment_id": core_tx.id,
        "payment_status": core_tx.status,
        "receipt_no": core_tx.receipt_no,
        "member_status": member.status if member else None,
        "membership_id": member.membership_id if member else None,
    }

