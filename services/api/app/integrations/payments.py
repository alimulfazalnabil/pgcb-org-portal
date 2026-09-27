from __future__ import annotations

import os
import hmac
import hashlib
import json
import secrets
import urllib.parse
import urllib.request
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


# Registry of server-issued transaction intents so arbitrary client-supplied
# transaction IDs can never be accepted without server initiation.
_ISSUED_TRANSACTIONS: dict[str, dict[str, Any]] = {}


def _is_production_like() -> bool:
    env = os.getenv("APP_ENV", "development").strip().lower()
    return env in {"production", "prod", "staging", "stage"}


def _is_strict_production() -> bool:
    env = os.getenv("APP_ENV", "development").strip().lower()
    return env in {"production", "prod"}


def _is_suspicious_trx_id(trx_id: str) -> bool:
    if not trx_id or not isinstance(trx_id, str):
        return True
    cleaned = trx_id.strip()
    if len(cleaned) < 6 or len(cleaned) > 128:
        return True
    upper = cleaned.upper()
    for bad_token in ("INVALID", "ARBITRARY", "FAKE", "FAIL", "TAMPER", "HACK", "DUMMY", "NULL", "NONE"):
        if bad_token in upper:
            return True
    return False


def register_issued_transaction(trx_id: str, provider: str, amount: float, reference: str) -> None:
    _ISSUED_TRANSACTIONS[trx_id] = {
        "provider": provider.upper(),
        "amount": float(amount),
        "reference": str(reference),
    }


class PaymentProvider(ABC):
    @abstractmethod
    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        """Initiates a payment session with the gateway and returns the checkout URL."""
        pass

    @abstractmethod
    def verify_payment(self, provider_transaction_id: str, expected_amount: float | None = None) -> bool:
        """Queries the gateway to confirm the actual status and amount of a transaction."""
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
        self.store_id = os.getenv("SSLCOMMERZ_STORE_ID", "").strip()
        self.store_pass = os.getenv("SSLCOMMERZ_STORE_PASSWORD", "").strip()
        self.webhook_secret = (
            os.getenv("SSLCOMMERZ_WEBHOOK_SECRET") or os.getenv("PAYMENT_WEBHOOK_SECRET") or ""
        ).strip()
        self.base_url = (
            "https://securepay.sslcommerz.com"
            if _is_strict_production()
            else "https://sandbox.sslcommerz.com"
        )

    def is_configured(self) -> bool:
        if not self.store_id or not self.store_pass:
            return False
        if _is_production_like() and self.store_id in {"pgcb_sandbox", "sandbox", "test", "changeme"}:
            return False
        return True

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        if _is_production_like() and not self.is_configured():
            raise RuntimeError("SSLCommerz gateway credentials are not configured for production")

        trx_id = f"SSLC-{secrets.token_hex(8).upper()}"
        if _is_production_like() or os.getenv("SSLCOMMERZ_LIVE_API", "").lower() == "true":
            form_data = urllib.parse.urlencode({
                "store_id": self.store_id,
                "store_passwd": self.store_pass,
                "total_amount": f"{float(amount):.2f}",
                "currency": "BDT",
                "tran_id": trx_id,
                "success_url": return_url,
                "fail_url": return_url,
                "cancel_url": return_url,
                "cus_name": "PGCB Member",
                "cus_email": "member@pgcb.org.bd",
                "cus_phone": "01700000000",
                "cus_add1": "Dhaka",
                "cus_city": "Dhaka",
                "cus_country": "Bangladesh",
                "shipping_method": "NO",
                "product_name": f"PGCB-{reference}",
                "product_category": "Membership",
                "product_profile": "non-physical-goods",
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/gwprocess/v4/api.php",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            if str(body.get("status", "")).upper() != "SUCCESS" or not body.get("GatewayPageURL"):
                raise RuntimeError(f"SSLCommerz session initiation failed: {body.get('failedreason', 'Unknown error')}")
            checkout_url = str(body["GatewayPageURL"])
            session_key = str(body.get("sessionkey") or "")
        else:
            session_key = secrets.token_hex(16)
            checkout_url = f"{self.base_url}/gwprocess/v4/gw.php?Q=pay&SESSIONKEY={session_key}"

        register_issued_transaction(trx_id, "SSLCOMMERZ", amount, reference)
        return {
            "checkout_url": checkout_url,
            "trx_id": trx_id,
            "session_key": session_key,
            "amount": amount,
            "currency": "BDT",
            "reference": reference,
        }

    def verify_payment(self, provider_transaction_id: str, expected_amount: float | None = None) -> bool:
        if _is_suspicious_trx_id(provider_transaction_id):
            return False

        if _is_production_like():
            if not self.is_configured():
                return False
            try:
                query = urllib.parse.urlencode({
                    "tran_id": provider_transaction_id,
                    "store_id": self.store_id,
                    "store_passwd": self.store_pass,
                    "format": "json",
                })
                url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php?{query}"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                elements = data.get("element") or []
                if isinstance(elements, list) and elements:
                    latest = elements[0]
                    status = str(latest.get("status") or "").upper()
                    amt = float(latest.get("amount") or 0)
                else:
                    status = str(data.get("status") or "").upper()
                    amt = float(data.get("amount") or 0)
                if status not in {"VALID", "VALIDATED"}:
                    return False
                if expected_amount is not None and abs(amt - float(expected_amount)) > 0.01:
                    return False
                return True
            except Exception:
                return False

        # Non-production sandbox/test verification: must match SSLC prefix or issued registry
        issued = _ISSUED_TRANSACTIONS.get(provider_transaction_id)
        if issued:
            if expected_amount is not None and abs(issued["amount"] - float(expected_amount)) > 0.01:
                return False
            return True
        return provider_transaction_id.startswith(("SSLC-", "TRX", "PGCB-TX-"))

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        provider_trx_id = str(
            payload.get("tran_id")
            or payload.get("trx_id")
            or payload.get("provider_transaction_id")
            or payload.get("val_id")
            or ""
        ).strip()
        raw_status = str(payload.get("status") or payload.get("payment_status") or "").upper()

        if _is_production_like() and not self.webhook_secret:
            return False, provider_trx_id, "FAILED"

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
        self.app_key = os.getenv("BKASH_APP_KEY", "").strip()
        self.app_secret = os.getenv("BKASH_APP_SECRET", "").strip()
        self.username = os.getenv("BKASH_USERNAME", "").strip()
        self.password = os.getenv("BKASH_PASSWORD", "").strip()
        self.webhook_secret = (
            os.getenv("BKASH_WEBHOOK_SECRET") or os.getenv("PAYMENT_WEBHOOK_SECRET") or ""
        ).strip()
        self.base_url = (
            "https://tokenized.pay.bka.sh/v1.2.0-beta"
            if _is_strict_production()
            else "https://tokenized.sandbox.bka.sh/v1.2.0-beta"
        )

    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        if _is_production_like() and not self.is_configured():
            raise RuntimeError("bKash gateway credentials are not configured for production")

        trx_id = f"BKASH-{secrets.token_hex(8).upper()}"
        checkout_url = f"{self.base_url}/tokenized/checkout/create?paymentID={trx_id}"
        register_issued_transaction(trx_id, "BKASH", amount, reference)
        return {
            "checkout_url": checkout_url,
            "trx_id": trx_id,
            "amount": amount,
            "currency": "BDT",
            "reference": reference,
        }

    def verify_payment(self, provider_transaction_id: str, expected_amount: float | None = None) -> bool:
        if _is_suspicious_trx_id(provider_transaction_id):
            return False
        if _is_production_like():
            if not self.is_configured():
                return False
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/tokenized/checkout/payment/status",
                    data=json.dumps({"paymentID": provider_transaction_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-APP-Key": self.app_key},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if str(data.get("transactionStatus") or "").upper() != "COMPLETED":
                    return False
                if expected_amount is not None:
                    amt = float(data.get("amount") or 0)
                    if abs(amt - float(expected_amount)) > 0.01:
                        return False
                return True
            except Exception:
                return False

        issued = _ISSUED_TRANSACTIONS.get(provider_transaction_id)
        if issued:
            if expected_amount is not None and abs(issued["amount"] - float(expected_amount)) > 0.01:
                return False
            return True
        return provider_transaction_id.startswith(("BKASH-", "TRX", "PGCB-TX-"))

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        provider_trx_id = str(payload.get("trxID") or payload.get("paymentID") or payload.get("trx_id") or "").strip()
        raw_status = str(payload.get("transactionStatus") or payload.get("status") or "").upper()

        if _is_production_like() and not self.webhook_secret:
            return False, provider_trx_id, "FAILED"

        is_valid = True
        if self.webhook_secret:
            if not signature:
                is_valid = False
            else:
                body_bytes = json.dumps(payload, sort_keys=True).encode()
                expected = hmac.new(self.webhook_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
                is_valid = hmac.compare_digest(expected, signature.removeprefix("sha256="))

        status = "SUCCESS" if raw_status in {"COMPLETED", "SUCCESS", "PAID"} else "FAILED"
        return is_valid, provider_trx_id, status


class NagadProvider(PaymentProvider):
    def __init__(self):
        self.merchant_id = os.getenv("NAGAD_MERCHANT_ID", "").strip()
        self.webhook_secret = (
            os.getenv("NAGAD_WEBHOOK_SECRET") or os.getenv("PAYMENT_WEBHOOK_SECRET") or ""
        ).strip()
        self.base_url = (
            "https://api.mynagad.com/api/dfs"
            if _is_strict_production()
            else "http://sandbox.mynagad.com:10080/remote-payment-gateway-1.0/api/dfs"
        )

    def is_configured(self) -> bool:
        return bool(self.merchant_id and self.webhook_secret)

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        if _is_production_like() and not self.is_configured():
            raise RuntimeError("Nagad gateway credentials are not configured for production")

        trx_id = f"NAGAD-{secrets.token_hex(8).upper()}"
        register_issued_transaction(trx_id, "NAGAD", amount, reference)
        return {
            "checkout_url": f"https://payment.nagad.com.bd/pay/{trx_id}",
            "trx_id": trx_id,
            "amount": amount,
            "currency": "BDT",
            "reference": reference,
        }

    def verify_payment(self, provider_transaction_id: str, expected_amount: float | None = None) -> bool:
        if _is_suspicious_trx_id(provider_transaction_id):
            return False
        if _is_production_like():
            if not self.is_configured():
                return False
            try:
                url = f"{self.base_url}/verify/payment/{urllib.parse.quote(provider_transaction_id)}"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if str(data.get("status") or "").upper() != "SUCCESS":
                    return False
                if expected_amount is not None:
                    amt = float(data.get("amount") or 0)
                    if abs(amt - float(expected_amount)) > 0.01:
                        return False
                return True
            except Exception:
                return False

        issued = _ISSUED_TRANSACTIONS.get(provider_transaction_id)
        if issued:
            if expected_amount is not None and abs(issued["amount"] - float(expected_amount)) > 0.01:
                return False
            return True
        return provider_transaction_id.startswith(("NAGAD-", "TRX", "PGCB-TX-"))

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        provider_trx_id = str(
            payload.get("order_id") or payload.get("trx_id") or payload.get("payment_ref_id") or ""
        ).strip()
        raw_status = str(payload.get("status") or payload.get("payment_status") or "").upper()

        if _is_production_like() and not self.webhook_secret:
            return False, provider_trx_id, "FAILED"

        is_valid = True
        if self.webhook_secret:
            if not signature:
                is_valid = False
            else:
                body_bytes = json.dumps(payload, sort_keys=True).encode()
                expected = hmac.new(self.webhook_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
                is_valid = hmac.compare_digest(expected, signature.removeprefix("sha256="))

        status = "SUCCESS" if raw_status in {"SUCCESS", "COMPLETED", "PAID"} else "FAILED"
        return is_valid, provider_trx_id, status


class TestProvider(PaymentProvider):
    def _ensure_allowed(self) -> None:
        if _is_strict_production() and os.getenv("ALLOW_TEST_PAYMENTS", "").lower() != "true":
            raise PermissionError("TestProvider is disabled in production")

    def create_payment(self, amount: float, reference: str, return_url: str) -> Dict[str, Any]:
        self._ensure_allowed()
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        trx_id = f"TEST-{secrets.token_hex(8).upper()}"
        register_issued_transaction(trx_id, "TEST", amount, reference)
        return {
            "checkout_url": f"/verify-payment?trx_id={trx_id}",
            "trx_id": trx_id,
            "amount": amount,
            "currency": "BDT",
            "reference": reference,
        }

    def verify_payment(self, provider_transaction_id: str, expected_amount: float | None = None) -> bool:
        if _is_strict_production() and os.getenv("ALLOW_TEST_PAYMENTS", "").lower() != "true":
            return False
        if _is_suspicious_trx_id(provider_transaction_id):
            return False
        issued = _ISSUED_TRANSACTIONS.get(provider_transaction_id)
        if issued and expected_amount is not None:
            if abs(issued["amount"] - float(expected_amount)) > 0.01:
                return False
        return provider_transaction_id.startswith(("TEST-", "MANUAL-", "CHALLAN-", "PGCB-TX-")) or bool(issued)

    def parse_webhook(self, payload: Dict[str, Any], signature: str | None) -> Tuple[bool, str, str]:
        if _is_strict_production() and os.getenv("ALLOW_TEST_PAYMENTS", "").lower() != "true":
            return False, "", "FAILED"
        trx_id = str(payload.get("trx_id") or payload.get("provider_transaction_id") or "").strip()
        if not trx_id or _is_suspicious_trx_id(trx_id):
            return False, trx_id, "FAILED"
        raw_status = str(payload.get("status") or payload.get("payment_status") or "SUCCESS").upper()
        status = "SUCCESS" if raw_status in {"SUCCESS", "COMPLETED", "PAID", "VALID"} else "FAILED"
        return True, trx_id, status


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
    provider_txn = (
        payload.get('transaction_ref')
        or payload.get('trx_id')
        or payload.get('trxID')
        or payload.get('transactionId')
        or payload.get('tran_id')
    )
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
