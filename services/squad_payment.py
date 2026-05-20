"""
services/squad_payment.py
Squad payment gateway — hosted checkout + webhook signature verification
Based on official Squad documentation
"""

import os
import uuid
import hmac
import hashlib
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY", "")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_CALLBACK_URL = os.getenv("SQUAD_CALLBACK_URL", "https://farmpay-gold.vercel.app/payment-success")


def generate_transaction_ref() -> str:
    """Generate unique transaction reference"""
    return f"FARMPAY-{uuid.uuid4().hex[:12].upper()}"


def _get_headers():
    """Get standard headers for Squad API calls"""
    return {
        "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initiate_payment(
    amount_kobo: int,
    buyer_email: str,
    buyer_name: str,
    transaction_ref: str = None,
) -> dict:
    """
    Initiate a payment session - returns hosted checkout URL
    Money will settle in your Squad merchant wallet
    """
    if transaction_ref is None:
        transaction_ref = generate_transaction_ref()

    payload = {
        "amount": amount_kobo,
        "email": buyer_email,
        "currency": "NGN",
        "initiate_type": "inline",
        "transaction_ref": transaction_ref,
        "callback_url": SQUAD_CALLBACK_URL,
        "customer_name": buyer_name,
        "payment_channels": ["card", "bank", "ussd", "transfer"],
        "pass_charge": False,
    }

    response = requests.post(
        f"{SQUAD_BASE_URL}/transaction/initiate",
        json=payload,
        headers=_get_headers(),
        timeout=30,
    )

    if response.status_code == 401:
        raise Exception("Squad API: Unauthorized - Invalid API key")
    elif response.status_code == 403:
        raise Exception("Squad API: Forbidden - API key format invalid")
    elif response.status_code != 200:
        raise Exception(f"Squad API error: {response.status_code} - {response.text}")

    data = response.json()

    if not data.get("success"):
        raise Exception(f"Squad API failed: {data.get('message')}")

    return {
        "transaction_ref": data["data"]["transaction_ref"],
        "checkout_url": data["data"]["checkout_url"],
        "amount_kobo": data["data"]["transaction_amount"],
        "currency": data["data"]["currency"],
    }


def verify_payment(transaction_ref: str) -> dict:
    """
    Verify payment status - call this after checkout completes
    """
    response = requests.get(
        f"{SQUAD_BASE_URL}/transaction/verify/{transaction_ref}",
        headers=_get_headers(),
        timeout=30,
    )

    if response.status_code == 400:
        return {"valid": False, "error": "Invalid transaction reference"}
    elif response.status_code == 401:
        raise Exception("Squad API: Unauthorized")
    elif response.status_code == 403:
        raise Exception("Squad API: Forbidden - Invalid API key")
    elif response.status_code != 200:
        raise Exception(f"Squad API error: {response.status_code}")

    data = response.json()

    if data.get("status") == 200 and data.get("success"):
        transaction_status = data["data"].get("transaction_status", "")
        return {
            "valid": True,
            "is_successful": str(transaction_status).strip().lower() == "success",
            "transaction_status": transaction_status,
            "amount_kobo": data["data"].get("transaction_amount"),
            "email": data["data"].get("email"),
        }

    return {"valid": False, "error": data.get("message", "Unknown error")}


def get_wallet_balance() -> dict:
    """
    Get Squad wallet balance (returns in Kobo)
    """
    response = requests.get(
        f"{SQUAD_BASE_URL}/merchant/balance?currency_id=NGN",
        headers=_get_headers(),
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get balance: {response.text}")

    data = response.json()
    return {
        "balance_kobo": int(data.get("data", {}).get("balance", 0)),
        "balance_naira": int(data.get("data", {}).get("balance", 0)) / 100,
        "currency": data.get("data", {}).get("currency_id"),
    }


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """
    Verify Squad webhook signature using x-squad-encrypted-body header
    Squad uses HMAC-SHA512 on the raw body
    """
    if not SQUAD_SECRET_KEY or not signature:
        logger.warning("Missing secret key or signature for webhook verification")
        return False

    try:
        expected = hmac.new(
            SQUAD_SECRET_KEY.encode('utf-8'),
            raw_body,
            hashlib.sha512
        ).hexdigest().upper()

        return hmac.compare_digest(expected, signature.upper())
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False