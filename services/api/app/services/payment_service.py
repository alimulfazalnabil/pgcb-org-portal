"""
Institutional Payment Service & Multi-Provider Abstraction for PGCB Portal.
Supports bKash, Nagad, SSLCommerz, and Manual Bank Payment (Challan/Deposit slip)
with server-side verification, amount validation, receipt generation, and membership activation.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.integrations.payments import (
    _is_production_like,
    _is_suspicious_trx_id,
    get_payment_provider as get_gateway_provider,
    register_issued_transaction,
)
from app.models import Member, PaymentTransaction, User
from app.services import audit, notify
from app.services.email import EmailService
from app.services.receipt_service import (
    activate_membership_from_payment,
    ensure_receipt_metadata,
    resolve_plan_amount,
)

TRANSACTION_STATES = {
    'INITIATED',
    'PENDING',
    'PROCESSING',
    'SUCCESS',
    'PAID',
    'FAILED',
    'CANCELLED',
    'EXPIRED',
    'REFUNDED',
}

ALLOWED_PAYMENT_TRANSITIONS: dict[str, set[str]] = {
    'INITIATED': {'PENDING', 'PROCESSING', 'SUCCESS', 'PAID', 'FAILED', 'CANCELLED', 'EXPIRED'},
    'PENDING': {'PROCESSING', 'SUCCESS', 'PAID', 'FAILED', 'CANCELLED', 'EXPIRED'},
    'PROCESSING': {'SUCCESS', 'PAID', 'FAILED', 'CANCELLED', 'EXPIRED'},
    'SUCCESS': {'REFUNDED'},
    'PAID': {'REFUNDED'},
    'FAILED': set(),
    'CANCELLED': set(),
    'EXPIRED': set(),
    'REFUNDED': set(),
}


def validate_payment_transition(current_status: str, target_status: str) -> bool:
    cur = (current_status or 'INITIATED').strip().upper()
    tgt = (target_status or '').strip().upper()
    if cur == tgt and cur in {'INITIATED', 'PENDING', 'PROCESSING'}:
        return True
    return tgt in ALLOWED_PAYMENT_TRANSITIONS.get(cur, set())


def transition_payment_status(trx: PaymentTransaction, target_status: str) -> None:
    cur = (trx.status or 'INITIATED').strip().upper()
    tgt = (target_status or '').strip().upper()
    if not validate_payment_transition(cur, tgt):
        raise HTTPException(409, f'Illegal payment state transition: {cur} -> {tgt}')
    trx.status = tgt


class PaymentProvider(ABC):
    @abstractmethod
    def initiate_payment(self, transaction: PaymentTransaction, redirect_url: str) -> dict:
        pass

    @abstractmethod
    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        pass


class BKashProvider(PaymentProvider):
    def initiate_payment(self, transaction: PaymentTransaction, redirect_url: str) -> dict:
        ref = transaction.transaction_ref or str(transaction.id)
        gw = get_gateway_provider("BKASH")
        if _is_production_like() and hasattr(gw, "is_configured") and not gw.is_configured():
            raise HTTPException(503, "bKash payment gateway credentials are not configured for production")
        register_issued_transaction(ref, "BKASH", float(transaction.amount), str(transaction.id))
        return {
            'payment_url': f"https://payment.bkash.com/checkout?trx={ref}",
            'provider': 'BKASH',
            'transaction_id': ref,
            'amount': transaction.amount,
        }

    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        raw_status = str(payload.get('status') or payload.get('transactionStatus') or 'SUCCESS').upper()
        if raw_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR', 'EXPIRED'}:
            return {'success': False, 'provider_transaction_id': None, 'status': raw_status, 'message': 'bKash payment failed or cancelled'}

        if 'amount' in payload and payload['amount'] is not None:
            try:
                if abs(float(payload['amount']) - float(transaction.amount)) > 0.01:
                    return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Payment amount mismatch'}
            except (TypeError, ValueError):
                return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Invalid payment amount'}

        provider_trx_id = payload.get('trxID') or payload.get('trx_id') or payload.get('provider_transaction_id')
        if not provider_trx_id or _is_suspicious_trx_id(str(provider_trx_id)):
            return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Missing or invalid bKash transaction ID'}

        gw = get_gateway_provider("BKASH")
        if not gw.verify_payment(str(provider_trx_id), expected_amount=float(transaction.amount)):
            return {'success': False, 'provider_transaction_id': provider_trx_id, 'status': 'FAILED', 'message': 'bKash server-side verification failed'}

        return {
            'success': True,
            'provider_transaction_id': str(provider_trx_id),
            'status': 'SUCCESS',
            'message': 'bKash payment verified successfully',
        }


class NagadProvider(PaymentProvider):
    def initiate_payment(self, transaction: PaymentTransaction, redirect_url: str) -> dict:
        ref = transaction.transaction_ref or str(transaction.id)
        gw = get_gateway_provider("NAGAD")
        if _is_production_like() and hasattr(gw, "is_configured") and not gw.is_configured():
            raise HTTPException(503, "Nagad payment gateway credentials are not configured for production")
        register_issued_transaction(ref, "NAGAD", float(transaction.amount), str(transaction.id))
        return {
            'payment_url': f"https://payment.nagad.com.bd/checkout?order={ref}",
            'provider': 'NAGAD',
            'transaction_id': ref,
            'amount': transaction.amount,
        }

    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        raw_status = str(payload.get('status') or payload.get('payment_status') or 'SUCCESS').upper()
        if raw_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR', 'EXPIRED'}:
            return {'success': False, 'provider_transaction_id': None, 'status': raw_status, 'message': 'Nagad payment failed or cancelled'}

        if 'amount' in payload and payload['amount'] is not None:
            try:
                if abs(float(payload['amount']) - float(transaction.amount)) > 0.01:
                    return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Payment amount mismatch'}
            except (TypeError, ValueError):
                return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Invalid payment amount'}

        provider_trx_id = payload.get('issuer_trx_id') or payload.get('order_id') or payload.get('trx_id') or payload.get('provider_transaction_id')
        if not provider_trx_id or _is_suspicious_trx_id(str(provider_trx_id)):
            return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Missing or invalid Nagad transaction ID'}

        gw = get_gateway_provider("NAGAD")
        if not gw.verify_payment(str(provider_trx_id), expected_amount=float(transaction.amount)):
            return {'success': False, 'provider_transaction_id': provider_trx_id, 'status': 'FAILED', 'message': 'Nagad server-side verification failed'}

        return {
            'success': True,
            'provider_transaction_id': str(provider_trx_id),
            'status': 'SUCCESS',
            'message': 'Nagad payment verified successfully',
        }


class SSLCommerzServiceProvider(PaymentProvider):
    def initiate_payment(self, transaction: PaymentTransaction, redirect_url: str) -> dict:
        ref = transaction.transaction_ref or str(transaction.id)
        gw = get_gateway_provider("SSLCOMMERZ")
        if _is_production_like() and hasattr(gw, "is_configured") and not gw.is_configured():
            raise HTTPException(503, "SSLCommerz payment gateway credentials are not configured for production")
        res = gw.create_payment(float(transaction.amount), ref, redirect_url)
        return {
            'payment_url': res.get('checkout_url'),
            'provider': 'SSLCOMMERZ',
            'transaction_id': res.get('trx_id', ref),
            'amount': transaction.amount,
        }

    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        raw_status = str(payload.get('status') or payload.get('payment_status') or 'VALID').upper()
        if raw_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR', 'EXPIRED'}:
            return {'success': False, 'provider_transaction_id': None, 'status': raw_status, 'message': 'SSLCommerz payment failed'}

        if 'amount' in payload and payload['amount'] is not None:
            try:
                if abs(float(payload['amount']) - float(transaction.amount)) > 0.01:
                    return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Payment amount mismatch'}
            except (TypeError, ValueError):
                return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Invalid payment amount'}

        provider_trx_id = payload.get('tran_id') or payload.get('val_id') or payload.get('trx_id') or payload.get('provider_transaction_id')
        if not provider_trx_id or _is_suspicious_trx_id(str(provider_trx_id)):
            return {'success': False, 'provider_transaction_id': None, 'status': 'FAILED', 'message': 'Missing or invalid SSLCommerz transaction ID'}

        gw = get_gateway_provider("SSLCOMMERZ")
        if not gw.verify_payment(str(provider_trx_id), expected_amount=float(transaction.amount)):
            return {'success': False, 'provider_transaction_id': provider_trx_id, 'status': 'FAILED', 'message': 'SSLCommerz verification failed'}

        return {
            'success': True,
            'provider_transaction_id': str(provider_trx_id),
            'status': 'SUCCESS',
            'message': 'SSLCommerz payment verified successfully',
        }


class ManualBankProvider(PaymentProvider):
    def initiate_payment(self, transaction: PaymentTransaction, redirect_url: str) -> dict:
        ref = transaction.transaction_ref or str(transaction.id)
        return {
            'provider': 'MANUAL_BANK',
            'transaction_id': ref,
            'amount': transaction.amount,
            'instructions': 'দয়া করে ব্যাংক ডিপোজিট স্লিপ বা চালানের স্ক্যান কপি সংযোজন করুন।',
        }

    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        challan_no = str(payload.get('challan_no') or '').strip()
        if _is_production_like() and not challan_no:
            return {
                'success': False,
                'provider_transaction_id': None,
                'status': 'FAILED',
                'message': 'Challan number is required for manual bank reconciliation in production',
            }
        if challan_no and _is_suspicious_trx_id(challan_no):
            return {
                'success': False,
                'provider_transaction_id': challan_no,
                'status': 'FAILED',
                'message': 'Invalid challan reference',
            }
        challan_no = challan_no or f"CHALLAN-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        return {
            'success': True,
            'provider_transaction_id': challan_no,
            'status': 'SUCCESS',
            'message': 'Manual bank deposit reconciled',
        }


class PaymentService:
    _providers = {
        'BKASH': BKashProvider(),
        'NAGAD': NagadProvider(),
        'SSLCOMMERZ': SSLCommerzServiceProvider(),
        'MANUAL_BANK': ManualBankProvider(),
        'MANUAL': ManualBankProvider(),
    }

    @classmethod
    def get_provider(cls, method: str) -> PaymentProvider:
        provider = cls._providers.get(method.upper())
        if not provider:
            raise HTTPException(400, f'Unsupported payment method: {method}')
        return provider

    @classmethod
    def create_transaction(
        cls,
        db: Session,
        user: User,
        amount: float | None = None,
        purpose: str = 'MEMBERSHIP_FEE',
        method: str = 'BKASH',
        reference_id: str | None = None,
        ip: str | None = None,
        membership_plan_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[PaymentTransaction, dict]:
        # 1. Idempotency check: if idempotency_key was already processed, return existing transaction
        if idempotency_key:
            existing_trx = db.scalar(
                select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idempotency_key)
            )
            if existing_trx:
                provider = cls.get_provider(existing_trx.provider)
                return existing_trx, provider.initiate_payment(existing_trx, redirect_url='/portal')

        # 2. Server-side plan fee calculation (Never trust client amount when membership_plan_id is supplied)
        if membership_plan_id:
            try:
                server_amount = resolve_plan_amount(db, membership_plan_id)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            if amount is not None and int(amount) != int(server_amount):
                raise HTTPException(
                    400,
                    f'Client amount (৳{amount}) does not match server-calculated fee (৳{server_amount}) for plan {membership_plan_id}',
                )
            amount = float(server_amount)

        if amount is None or amount <= 0:
            raise HTTPException(400, 'Payment amount must be greater than zero')

        member = db.scalar(select(Member).where(Member.user_id == user.id))
        trx_ref = f"PGCB-TX-{datetime.utcnow().year}-{uuid4().hex[:10].upper()}"
        trx = PaymentTransaction(
            transaction_ref=trx_ref,
            user_id=user.id,
            member_id=member.id if member else None,
            membership_plan_id=membership_plan_id.upper() if membership_plan_id else None,
            idempotency_key=idempotency_key,
            amount=int(amount),
            currency='BDT',
            purpose=purpose,
            provider=method.upper(),
            status='INITIATED',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(trx)
        db.flush()

        audit(db, user, 'INITIATE_PAYMENT', 'PAYMENT', trx.id, ip)
        db.commit()
        db.refresh(trx)

        provider = cls.get_provider(method)
        checkout_data = provider.initiate_payment(trx, redirect_url='/portal')
        return trx, checkout_data

    @classmethod
    def complete_transaction(
        cls,
        db: Session,
        transaction_id: str,
        provider_payload: dict,
        actor_user: User | None = None,
        ip: str | None = None,
    ) -> PaymentTransaction:
        trx = db.scalar(
            select(PaymentTransaction).where(
                (PaymentTransaction.transaction_ref == transaction_id) |
                (PaymentTransaction.id == int(transaction_id) if str(transaction_id).isdigit() else False)
            )
        )
        if not trx:
            raise HTTPException(404, 'Transaction not found')

        incoming_status = str(
            provider_payload.get('status')
            or provider_payload.get('transactionStatus')
            or provider_payload.get('payment_status')
            or 'SUCCESS'
        ).strip().upper()
        is_failure_attempt = incoming_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR', 'EXPIRED'}

        # Enforce strict state machine: a completed (SUCCESS/PAID) transaction cannot transition to FAILED/CANCELLED
        if trx.status in ('SUCCESS', 'PAID'):
            if is_failure_attempt:
                raise HTTPException(409, f'Illegal payment state transition: {trx.status} -> {incoming_status}')
            return trx

        # If transaction is already in a terminal failure/refunded state, forbid re-completing via callback
        if trx.status in ('FAILED', 'CANCELLED', 'EXPIRED', 'REFUNDED'):
            raise HTTPException(409, f'Illegal payment state transition from terminal state: {trx.status}')

        provider = cls.get_provider(trx.provider)
        verification = provider.verify_payment(trx, provider_payload)

        if verification.get('success'):
            prov_trx_id = verification.get('provider_transaction_id')
            if prov_trx_id:
                duplicate_owner = db.scalar(
                    select(PaymentTransaction).where(
                        PaymentTransaction.provider_transaction_id_col == str(prov_trx_id),
                        PaymentTransaction.id != trx.id,
                    )
                )
                if duplicate_owner:
                    raise HTTPException(409, 'Duplicate provider_transaction_id already processed for another transaction')
                trx.provider_transaction_id = str(prov_trx_id)

            transition_payment_status(trx, 'SUCCESS')
            merged_payload = dict(provider_payload or {})
            if prov_trx_id:
                merged_payload.setdefault('trxID', prov_trx_id)
            trx.provider_payload = merged_payload
            trx.updated_at = datetime.utcnow()
            ensure_receipt_metadata(trx)
            activate_membership_from_payment(db, trx)
            audit(db, actor_user, 'COMPLETE_PAYMENT', 'PAYMENT', trx.id, ip)

            user = db.get(User, trx.user_id) if trx.user_id else None
            if user and trx.purpose not in {'MEMBERSHIP', 'MEMBERSHIP_FEE', 'RENEWAL', 'APPLICATION'}:
                notify(
                    db,
                    user.id,
                    'পেমেন্ট সফল হয়েছে',
                    f'আপনার ৳{trx.amount} টাকার পেমেন্ট সফলভাবে জমা হয়েছে (রেফারেন্স: {trx.transaction_ref}, রসিদ: {trx.receipt_no})।',
                    'PAYMENT',
                )
                EmailService.send_payment_receipt(
                    to_email=user.email,
                    payer_name=user.name_bn or user.name_en or 'প্রকৌশলী',
                    amount=f"৳{trx.amount:,.2f}",
                    transaction_id=trx.transaction_ref or str(trx.id),
                    purpose=trx.purpose,
                )
        else:
            target_fail_state = 'CANCELLED' if incoming_status in {'CANCELLED', 'CANCELED'} else ('EXPIRED' if incoming_status == 'EXPIRED' else 'FAILED')
            transition_payment_status(trx, target_fail_state)
            trx.updated_at = datetime.utcnow()
            audit(db, actor_user, 'FAILED_PAYMENT', 'PAYMENT', trx.id, ip)

        db.commit()
        db.refresh(trx)
        return trx

