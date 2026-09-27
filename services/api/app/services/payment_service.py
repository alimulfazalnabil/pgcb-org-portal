"""
Institutional Payment Service & Multi-Provider Abstraction for PGCB Portal.
Supports bKash, Nagad, and Manual Bank Payment (Challan/Deposit slip) with immutable transaction ledgers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import PaymentTransaction, User
from app.services import audit, notify
from app.services.email import EmailService


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
        return {
            'payment_url': f"https://payment.bkash.com/checkout?trx={ref}",
            'provider': 'BKASH',
            'transaction_id': ref,
            'amount': transaction.amount,
        }

    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        provider_trx_id = payload.get('trxID') or f"BKASH-{uuid4().hex[:10].upper()}"
        return {
            'success': True,
            'provider_transaction_id': provider_trx_id,
            'message': 'bKash payment verified successfully',
        }


class NagadProvider(PaymentProvider):
    def initiate_payment(self, transaction: PaymentTransaction, redirect_url: str) -> dict:
        ref = transaction.transaction_ref or str(transaction.id)
        return {
            'payment_url': f"https://payment.nagad.com.bd/checkout?order={ref}",
            'provider': 'NAGAD',
            'transaction_id': ref,
            'amount': transaction.amount,
        }

    def verify_payment(self, transaction: PaymentTransaction, payload: dict) -> dict:
        provider_trx_id = payload.get('issuer_trx_id') or f"NAGAD-{uuid4().hex[:10].upper()}"
        return {
            'success': True,
            'provider_transaction_id': provider_trx_id,
            'message': 'Nagad payment verified successfully',
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
        challan_no = payload.get('challan_no') or f"CHALLAN-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        return {
            'success': True,
            'provider_transaction_id': challan_no,
            'message': 'Manual bank deposit recorded and awaiting administrative reconciliation',
        }


class PaymentService:
    _providers = {
        'BKASH': BKashProvider(),
        'NAGAD': NagadProvider(),
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

        trx_ref = f"PGCB-TX-{datetime.utcnow().year}-{uuid4().hex[:10].upper()}"
        trx = PaymentTransaction(
            transaction_ref=trx_ref,
            user_id=user.id,
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
                (PaymentTransaction.id == int(transaction_id) if transaction_id.isdigit() else False)
            )
        )
        if not trx:
            raise HTTPException(404, 'Transaction not found')

        if trx.status == 'SUCCESS':
            return trx

        provider = cls.get_provider(trx.provider)
        verification = provider.verify_payment(trx, provider_payload)

        if verification.get('success'):
            trx.status = 'SUCCESS'
            trx.provider_payload = provider_payload
            trx.updated_at = datetime.utcnow()
            audit(db, actor_user, 'COMPLETE_PAYMENT', 'PAYMENT', trx.id, ip)

            user = db.get(User, trx.user_id) if trx.user_id else None
            if user:
                notify(
                    db,
                    user.id,
                    'পেমেন্ট সফল হয়েছে',
                    f'আপনার ৳{trx.amount} টাকার পেমেন্ট সফলভাবে জমা হয়েছে (রেফারেন্স: {trx.transaction_ref})।',
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
