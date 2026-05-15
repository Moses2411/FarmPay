"""
services/squad_payment.py
Squad payment gateway — hosted checkout + webhook signature verification.
"""

import os
import uuid
import hmac
import hashlib
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY", "")
SQUAD_PUBLIC_KEY = os.getenv("SQUAD_PUBLIC_KEY", "")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_CALLBACK_URL = os.getenv("SQUAD_CALLBACK_URL", "http://localhost:8000/payments/callback")


def generate_transaction_ref() -> str:
    return f"FARMPAY-{uuid.uuid4().hex[:12].upper()}"


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initiate_payment(
    amount_kobo: int,
    buyer_email: str,
    buyer_name: str,
    transaction_ref: str = None,
    payment_channels: list = None,
) -> dict:
    """
    Initiate a Squad hosted checkout session.
    Returns checkout_url for redirect.
    Money lands in YOUR Squad merchant wallet on completion.
    """
    if transaction_ref is None:
        transaction_ref = generate_transaction_ref()

    if payment_channels is None:
        payment_channels = ["card", "bank", "ussd", "transfer"]

    payload = {
        "amount": amount_kobo,
        "email": buyer_email,
        "currency": "NGN",
        "initiate_type": "inline",
        "transaction_ref": transaction_ref,
        "callback_url": SQUAD_CALLBACK_URL,
        "customer_name": buyer_name,
        "payment_channels": payment_channels,
        "pass_charge": False,
    }

    response = requests.post(
        f"{SQUAD_BASE_URL}/transaction/initiate",
        json=payload,
        headers=_get_headers(),
        timeout=30,
    )

    if response.status_code == 401:
        raise Exception("Squad API: Unauthorized — check SQUAD_SECRET_KEY")
    if response.status_code == 403:
        raise Exception("Squad API: Forbidden — API key format invalid")
    if response.status_code != 200:
        raise Exception(f"Squad API error [{response.status_code}]: {response.text}")

    data = response.json()
    if not data.get("success"):
        raise Exception(f"Squad initiate failed: {data.get('message')}")

    return {
        "transaction_ref": data["data"]["transaction_ref"],
        "checkout_url": data["data"]["checkout_url"],
        "transaction_amount": data["data"]["transaction_amount"],
        "authorized_channels": data["data"]["authorized_channels"],
        "currency": data["data"]["currency"],
        "merchant_id": data["data"]["merchant_info"]["merchant_id"],
    }


def verify_payment(transaction_ref: str) -> dict:
    """
    Server-side payment verification.
    Always call this — never trust client-side status.
    """
    response = requests.get(
        f"{SQUAD_BASE_URL}/transaction/verify/{transaction_ref}",
        headers=_get_headers(),
        timeout=30,
    )

    if response.status_code == 400:
        return {"valid": False, "error": "Invalid transaction reference"}
    if response.status_code == 401:
        raise Exception("Squad API: Unauthorized")
    if response.status_code != 200:
        raise Exception(f"Squad API error [{response.status_code}]: {response.text}")

    data = response.json()

    if data.get("status") == 200 and data.get("success"):
        return {
            "valid": True,
            "transaction_status": data["data"].get("transaction_status"),
            "amount": data["data"].get("transaction_amount"),
            "email": data["data"].get("email"),
            "transaction_type": data["data"].get("transaction_type"),
            "gateway_ref": data["data"].get("gateway_transaction_ref"),
            "currency": data["data"].get("transaction_currency_id"),
        }

    return {"valid": False, "error": data.get("message", "Unknown error")}


def verify_webhook_signature(raw_body: bytes, signature: str, secret_key: str) -> bool:
    """
    Verify Squad Dynamic VA webhook signature.
    Squad supports V1, V2, V3. We implement V3 (most secure):
      hash = HMAC-SHA512( txn_ref|va_number|currency|principal|settled|customer_id )

    Falls back to V1 (hash entire body) if V3 fields are absent.
    Always responds HTTP 200 to Squad to acknowledge receipt.
    """
    if not secret_key or not signature:
        return False

    try:
        data = json.loads(raw_body)
        body = data.get("Body", data.get("data", {}))

        # Attempt V3 signature
        txn_ref = body.get("transaction_ref", body.get("transaction_reference", ""))
        va_number = body.get("account_number", body.get("virtual_account_number", ""))
        currency = body.get("currency", "NGN")
        principal = str(body.get("principal_amount", body.get("amount", "0")))
        settled = str(body.get("settled_amount", "0"))
        customer_id = body.get("customer_identifier", "")

        if txn_ref and va_number:
            payload_string = f"{txn_ref}|{va_number}|{currency}|{principal}|{settled}|{customer_id}"
            expected_v3 = hmac.new(
                secret_key.encode("utf-8"),
                payload_string.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest().upper()

            if hmac.compare_digest(expected_v3, signature.upper()):
                return True

        # Fallback: V1 — hash entire raw body
        expected_v1 = hmac.new(
            secret_key.encode("utf-8"),
            raw_body,
            hashlib.sha512,
        ).hexdigest().upper()

        return hmac.compare_digest(expected_v1, signature.upper())

    except Exception as e:
        print(f"[SQUAD] Signature verification error: {e}")
        return False


def simulate_va_payment(virtual_account_number: str, amount_kobo: int) -> dict:
    """Sandbox only: simulate a payment into a virtual account."""
    response = requests.post(
        f"{SQUAD_BASE_URL}/virtual-account/simulate/payment",
        json={"virtual_account_number": virtual_account_number, "amount": amount_kobo},
        headers=_get_headers(),
        timeout=30,
    )
    data = response.json()
    if data.get("success"):
        return {"success": True, "message": data.get("message")}
    raise Exception(f"Simulation failed: {data.get('message')}")