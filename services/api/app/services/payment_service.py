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
from app.services.receipt_service import activate_membership_from_payment, ensure_receipt_metadata


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
        if raw_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR'}:
            return {'success': False, 'provider_transaction_id': None, 'message': 'bKash payment failed or cancelled'}

        if 'amount' in payload and payload['amount'] is not None:
            try:
                if abs(float(payload['amount']) - float(transaction.amount)) > 0.01:
                    return {'success': False, 'provider_transaction_id': None, 'message': 'Payment amount mismatch'}
            except (TypeError, ValueError):
                return {'success': False, 'provider_transaction_id': None, 'message': 'Invalid payment amount'}

        provider_trx_id = payload.get('trxID') or payload.get('trx_id') or payload.get('provider_transaction_id')
        if not provider_trx_id:
            if _is_production_like():
                return {'success': False, 'provider_transaction_id': None, 'message': 'Missing bKash transaction ID'}
            provider_trx_id = transaction.transaction_ref or f"BKASH-{uuid4().hex[:10].upper()}"
            register_issued_transaction(provider_trx_id, "BKASH", float(transaction.amount), str(transaction.id))

        gw = get_gateway_provider("BKASH")
        if not gw.verify_payment(str(provider_trx_id), expected_amount=float(transaction.amount)):
            return {'success': False, 'provider_transaction_id': provider_trx_id, 'message': 'bKash server-side verification failed'}

        return {
            'success': True,
            'provider_transaction_id': str(provider_trx_id),
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
        if raw_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR'}:
            return {'success': False, 'provider_transaction_id': None, 'message': 'Nagad payment failed or cancelled'}

        if 'amount' in payload and payload['amount'] is not None:
            try:
                if abs(float(payload['amount']) - float(transaction.amount)) > 0.01:
                    return {'success': False, 'provider_transaction_id': None, 'message': 'Payment amount mismatch'}
            except (TypeError, ValueError):
                return {'success': False, 'provider_transaction_id': None, 'message': 'Invalid payment amount'}

        provider_trx_id = payload.get('issuer_trx_id') or payload.get('order_id') or payload.get('trx_id')
        if not provider_trx_id:
            if _is_production_like():
                return {'success': False, 'provider_transaction_id': None, 'message': 'Missing Nagad transaction ID'}
            provider_trx_id = transaction.transaction_ref or f"NAGAD-{uuid4().hex[:10].upper()}"
            register_issued_transaction(provider_trx_id, "NAGAD", float(transaction.amount), str(transaction.id))

        gw = get_gateway_provider("NAGAD")
        if not gw.verify_payment(str(provider_trx_id), expected_amount=float(transaction.amount)):
            return {'success': False, 'provider_transaction_id': provider_trx_id, 'message': 'Nagad server-side verification failed'}

        return {
            'success': True,
            'provider_transaction_id': str(provider_trx_id),
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
        if raw_status in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR'}:
            return {'success': False, 'provider_transaction_id': None, 'message': 'SSLCommerz payment failed'}

        if 'amount' in payload and payload['amount'] is not None:
            try:
                if abs(float(payload['amount']) - float(transaction.amount)) > 0.01:
                    return {'success': False, 'provider_transaction_id': None, 'message': 'Payment amount mismatch'}
            except (TypeError, ValueError):
                return {'success': False, 'provider_transaction_id': None, 'message': 'Invalid payment amount'}

        provider_trx_id = payload.get('tran_id') or payload.get('val_id') or payload.get('trx_id') or transaction.transaction_ref
        gw = get_gateway_provider("SSLCOMMERZ")
        if not provider_trx_id or not gw.verify_payment(str(provider_trx_id), expected_amount=float(transaction.amount)):
            return {'success': False, 'provider_transaction_id': provider_trx_id, 'message': 'SSLCommerz verification failed'}

        return {
            'success': True,
            'provider_transaction_id': str(provider_trx_id),
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
                'message': 'Challan number is required for manual bank reconciliation in production',
            }
        if challan_no and _is_suspicious_trx_id(challan_no):
            return {
                'success': False,
                'provider_transaction_id': challan_no,
                'message': 'Invalid challan reference',
            }
        challan_no = challan_no or f"CHALLAN-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        return {
            'success': True,
            'provider_transaction_id': challan_no,
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
        amount: float,
        purpose: str,
        method: str = 'BKASH',
        reference_id: str | None = None,
        ip: str | None = None,
    ) -> tuple[PaymentTransaction, dict]:
        if amount <= 0:
            raise HTTPException(400, 'Payment amount must be greater than zero')

        member = db.scalar(select(Member).where(Member.user_id == user.id))
        trx_ref = f"PGCB-TX-{datetime.utcnow().year}-{uuid4().hex[:10].upper()}"
        trx = PaymentTransaction(
            transaction_ref=trx_ref,
            user_id=user.id,
            member_id=member.id if member else None,
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

        if trx.status in ('SUCCESS', 'PAID'):
            return trx

        provider = cls.get_provider(trx.provider)
        verification = provider.verify_payment(trx, provider_payload)

        if verification.get('success'):
            trx.status = 'SUCCESS'
            merged_payload = dict(provider_payload or {})
            if verification.get('provider_transaction_id'):
                merged_payload.setdefault('trxID', verification['provider_transaction_id'])
            trx.provider_payload = merged_payload
            trx.updated_at = datetime.utcnow()
            ensure_receipt_metadata(trx)
            activate_membership_from_payment(db, trx)
            audit(db, actor_user, 'COMPLETE_PAYMENT', 'PAYMENT', trx.id, ip)

            user = db.get(User, trx.user_id) if trx.user_id else None
            if user and trx.purpose not in {'MEMBERSHIP', 'RENEWAL', 'APPLICATION'}:
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
            trx.status = 'FAILED'
            trx.updated_at = datetime.utcnow()
            audit(db, actor_user, 'FAILED_PAYMENT', 'PAYMENT', trx.id, ip)

        db.commit()
        db.refresh(trx)
        return trx
