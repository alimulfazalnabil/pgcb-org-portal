from __future__ import annotations

import os
import hmac
import hashlib
import json
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any, Tuple


@dataclass(frozen=True)
class CheckoutIntent:
    provider: str
    provider_transaction_id: str
    checkout_url: str | None
    status: str = 'PENDING'
    raw: dict[str, Any] | None = None


class PaymentProvider(ABC):
    @abstractmethod
    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        """Initiates a payment session with the gateway and returns the checkout URL."""
        pass

    @abstractmethod
    def verify_payment(self, provider_transaction_id: str) -> bool:
        """Queries the gateway to confirm the actual status of a transaction."""
        pass

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        """
        Verifies webhook signature and extracts data.
        Returns: (is_valid, provider_transaction_id, status)
        """
        pass


class SSLCommerzProvider(PaymentProvider):
    def __init__(self):
        self.store_id = os.getenv("SSLCOMMERZ_STORE_ID", "pgcb_sandbox")
        self.store_pass = os.getenv("SSLCOMMERZ_STORE_PASSWORD", "pgcb_secret")
        self.webhook_secret = os.getenv("SSLCOMMERZ_WEBHOOK_SECRET") or os.getenv("PAYMENT_WEBHOOK_SECRET", "")
        self.base_url = "https://sandbox.sslcommerz.com" if os.getenv("APP_ENV") != "production" else "https://securepay.sslcommerz.com"

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        trx_id = f"SSLC-{secrets.token_hex(8).upper()}"
        session_key = secrets.token_hex(16)
        checkout_url = f"{self.base_url}/gwprocess/v4/gw.php?Q=pay&SESSIONKEY={session_key}"
        return {
            "checkout_url": checkout_url,
            "trx_id": trx_id,
            "session_key": session_key,
            "amount": amount,
            "currency": "BDT",
            "reference": reference
        }

    def verify_payment(self, provider_transaction_id: str) -> bool:
        # If in sandbox or mock, validate transaction format
        if not provider_transaction_id:
            return False
        # In production, query SSLCommerz Order Validation API
        return True

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        provider_trx_id = (
            payload.get("tran_id") or 
            payload.get("trx_id") or 
            payload.get("provider_transaction_id") or 
            payload.get("val_id") or ""
        )
        raw_status = str(payload.get("status") or payload.get("payment_status") or "").upper()
        
        # Verify HMAC signature when webhook secret is configured
        is_valid = True
        if self.webhook_secret:
            if not signature:
                is_valid = False
            else:
                body_bytes = json.dumps(payload, sort_keys=True).encode()
                expected = hmac.new(self.webhook_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
                is_valid = hmac.compare_digest(expected, signature.removeprefix("sha256="))
        
        status = "SUCCESS" if raw_status in {"VALID", "VALIDATED", "SUCCESS", "PAID", "COMPLETED"} else "FAILED"
        return is_valid, provider_trx_id, status


class BKashProvider(PaymentProvider):
    def __init__(self):
        self.app_key = os.getenv("BKASH_APP_KEY", "")
        self.app_secret = os.getenv("BKASH_APP_SECRET", "")
        self.webhook_secret = os.getenv("BKASH_WEBHOOK_SECRET") or os.getenv("PAYMENT_WEBHOOK_SECRET", "")
        self.base_url = "https://tokenized.sandbox.bka.sh/v1.2.0-beta" if os.getenv("APP_ENV") != "production" else "https://tokenized.pay.bka.sh/v1.2.0-beta"

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        trx_id = f"BKASH-{secrets.token_hex(8).upper()}"
        checkout_url = f"{self.base_url}/tokenized/checkout/create?paymentID={trx_id}"
        return {
            "checkout_url": checkout_url,
            "trx_id": trx_id,
            "amount": amount,
            "currency": "BDT",
            "reference": reference
        }

    def verify_payment(self, provider_transaction_id: str) -> bool:
        return bool(provider_transaction_id)

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        provider_trx_id = payload.get("trxID") or payload.get("paymentID") or payload.get("trx_id") or ""
        raw_status = str(payload.get("transactionStatus") or payload.get("status") or "").upper()
        
        is_valid = True
        if self.webhook_secret and signature:
            body_bytes = json.dumps(payload, sort_keys=True).encode()
            expected = hmac.new(self.webhook_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
            is_valid = hmac.compare_digest(expected, signature.removeprefix("sha256="))
        
        status = "SUCCESS" if raw_status in {"COMPLETED", "SUCCESS", "PAID"} else "FAILED"
        return is_valid, provider_trx_id, status


class NagadProvider(PaymentProvider):
    def __init__(self):
        self.merchant_id = os.getenv("NAGAD_MERCHANT_ID", "")
        self.webhook_secret = os.getenv("NAGAD_WEBHOOK_SECRET") or os.getenv("PAYMENT_WEBHOOK_SECRET", "")

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        trx_id = f"NAGAD-{secrets.token_hex(8).upper()}"
        return {
            "checkout_url": f"https://payment.nagad.com.bd/pay/{trx_id}",
            "trx_id": trx_id,
            "amount": amount,
            "currency": "BDT",
            "reference": reference
        }

    def verify_payment(self, provider_transaction_id: str) -> bool:
        return bool(provider_transaction_id)

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        provider_trx_id = payload.get("order_id") or payload.get("trx_id") or payload.get("payment_ref_id") or ""
        raw_status = str(payload.get("status") or payload.get("payment_status") or "").upper()
        status = "SUCCESS" if raw_status in {"SUCCESS", "COMPLETED", "PAID"} else "FAILED"
        return True, provider_trx_id, status


class TestProvider(PaymentProvider):
    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        trx_id = f"TEST-{secrets.token_hex(8).upper()}"
        return {
            "checkout_url": f"/verify-payment?trx_id={trx_id}",
            "trx_id": trx_id,
            "amount": amount,
            "currency": "BDT",
            "reference": reference
        }

    def verify_payment(self, provider_transaction_id: str) -> bool:
        return True

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        trx_id = payload.get("trx_id") or payload.get("provider_transaction_id") or f"TEST-{secrets.token_hex(4).upper()}"
        return True, trx_id, "SUCCESS"


def get_payment_provider(provider_type: str) -> PaymentProvider:
    """Factory pattern to fetch the requested provider."""
    normalized = provider_type.strip().upper()
    if normalized == "SSLCOMMERZ":
        return SSLCommerzProvider()
    elif normalized == "BKASH":
        return BKashProvider()
    elif normalized == "NAGAD":
        return NagadProvider()
    elif normalized in {"TEST", "MANUAL"}:
        return TestProvider()
    raise ValueError(f"Unsupported Payment Provider: {provider_type}")


# --- Backward Compatibility Helpers ---

def provider_secret(provider: str) -> str:
    normalized = provider.upper().replace('-', '_')
    return os.getenv(f'{normalized}_WEBHOOK_SECRET') or os.getenv('PAYMENT_WEBHOOK_SECRET', '')


def verify_hmac_signature(provider: str, body: bytes, signature: str | None) -> bool:
    secret = provider_secret(provider)
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    candidate = signature.removeprefix('sha256=')
    return hmac.compare_digest(expected, candidate)


def normalize_provider(provider: str) -> str:
    p = provider.strip().upper()
    allowed = {'MANUAL', 'TEST', 'BKASH', 'NAGAD', 'SSLCOMMERZ'}
    if p not in allowed:
        raise ValueError(f'Unsupported payment provider: {provider}')
    return p


def create_checkout(provider: str, payment_id: int, amount: int | float, currency: str) -> CheckoutIntent:
    p = normalize_provider(provider)
    service = get_payment_provider(p)
    res = service.create_payment(float(amount), str(payment_id), "/portal")
    return CheckoutIntent(
        p,
        res.get("trx_id", f"{p[:3]}-{secrets.token_hex(8).upper()}"),
        res.get("checkout_url"),
        raw={"amount": str(Decimal(str(amount))), "currency": currency}
    )


def parse_webhook(payload: dict[str, Any]) -> tuple[str | None, str | None, str]:
    event_id = payload.get('event_id') or payload.get('id') or payload.get('eventId')
    provider_txn = payload.get('transaction_ref') or payload.get('trx_id') or payload.get('trxID') or payload.get('transactionId') or payload.get('tran_id')
    status = str(payload.get('status') or payload.get('payment_status') or '').upper()
    return event_id, provider_txn, status


def payment_status_from_provider(status: str) -> str | None:
    s = status.upper()
    if s in {'SUCCESS', 'SUCCEEDED', 'PAID', 'COMPLETED', 'VALID', 'VALIDATED'}:
        return 'PAID'
    if s in {'FAILED', 'FAILURE', 'CANCELLED', 'CANCELED', 'DECLINED', 'ERROR'}:
        return 'FAILED'
    if s in {'REFUNDED', 'REFUND'}:
        return 'REFUNDED'
    if s in {'PENDING', 'INITIATED', 'PROCESSING'}:
        return 'PENDING'
    return None
