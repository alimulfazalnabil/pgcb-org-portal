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
            return {"status": "already_processed", "idempotent_replay": True, "receipt_no": core_tx.receipt_no}

        if gateway_status == "SUCCESS":
            if payment_service.verify_payment(provider_trx_id, expected_amount=float(core_tx.amount)):
                core_tx.provider_transaction_id = provider_trx_id
                transition_payment_status(core_tx, "PAID")
                ensure_receipt_metadata(core_tx)
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
        return {"status": "already_processed"}

    if gateway_status == "SUCCESS":
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

    purpose_en_map = {
        'MEMBERSHIP': 'Membership Fee',
        'MEMBERSHIP_FEE': 'Membership Fee',
        'RENEWAL': 'Membership Renewal Fee',
        'APPLICATION': 'Membership Application Fee',
        'EVENT': 'Event Registration Fee',
        'DONATION': 'Welfare Contribution',
    }
    purpose_bn_map = {
        'MEMBERSHIP': 'সদস্যপদ ফি',
        'MEMBERSHIP_FEE': 'সদস্যপদ ফি',
        'RENEWAL': 'সদস্যপদ নবায়ন ফি',
        'APPLICATION': 'সদস্যপদ আবেদন ফি',
        'EVENT': 'ইভেন্ট নিবন্ধন ফি',
        'DONATION': 'কল্যাণ তহবিল অনুদান',
    }

    result = []
    for p in rows:
        purpose_key = (p.purpose or 'MEMBERSHIP').upper()
        is_paid = p.status in ('PAID', 'SUCCESS', 'COMPLETED')
        created_dt = p.created_at or datetime.utcnow()
        result.append(
            {
                'id': p.id,
                'date': created_dt.strftime('%Y-%m-%d'),
                'purpose': purpose_key,
                'purpose_label': purpose_en_map.get(purpose_key, 'Membership Fee'),
                'purpose_label_bn': purpose_bn_map.get(purpose_key, 'সদস্যপদ ফি'),
                'membership_plan_id': p.membership_plan_id,
                'amount': float(p.amount),
                'amount_formatted': f"৳{int(p.amount):,}",
                'currency': p.currency,
                'provider': p.provider,
                'transaction_ref': p.transaction_ref,
                'receipt_no': p.receipt_no,
                'status': 'PAID' if is_paid else p.status,
                'has_receipt': is_paid,
                'receipt_url': f"/api/v1/member/payments/{p.id}/receipt" if is_paid else None,
                'receipt_pdf_url': f"/api/v1/member/payments/{p.id}/receipt.pdf" if is_paid else None,
                'created_at': p.created_at,
            }
        )
    return result


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
    if not is_owner and user.role == "MEMBER":
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
    activate_membership_from_payment(db, core_tx)

    webhook_log = PaymentWebhook(
        provider=PaymentProviderType.BKASH,
        payload={"sandbox_simulation": True, "payment_id": core_tx.id, "trxID": sim_trx_id},
        is_processed=True,
    )
    db.add(webhook_log)

    from app.models import Membership, Payment as CanonicalPayment
    if not db.scalar(select(CanonicalPayment).where(CanonicalPayment.transaction_id == sim_trx_id)):
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

