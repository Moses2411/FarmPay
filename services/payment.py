"""
services/payment.py
Handles: initiate checkout, verify transaction.
"""

import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_CALLBACK_URL = os.getenv("SQUAD_CALLBACK_URL", "http://127.0.0.1:8000/payments/callback")

_HEADERS = {
    "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
    "Content-Type": "application/json",
}


def generate_transaction_ref() -> str:
    """Unique ref prefixed with FARMPAY."""
    return f"FARMPAY-{uuid.uuid4().hex[:12].upper()}"


def initiate_payment(amount_naira: float, buyer_email: str, buyer_name: str) -> dict:
    """
    Calls Squad /transaction/initiate.
    Returns a dict with checkout_url and transaction_ref for the frontend.
    Amount must be in kobo (naira × 100).
    """
    amount_kobo = int(amount_naira * 100)
    transaction_ref = generate_transaction_ref()

    payload = {
        "amount": amount_kobo,
        "email": buyer_email,
        "currency": "NGN",
        "initiate_type": "inline",
        "transaction_ref": transaction_ref,
        "callback_url": SQUAD_CALLBACK_URL,
        "pass_charge": False,           # merchant absorbs Squad fee
        "customer_name": buyer_name,
        "payment_channels": ["card", "bank", "ussd", "transfer"],
        "metadata": {
            "source": "FarmPay",
        },
    }

    response = requests.post(
        f"{SQUAD_BASE_URL}/transaction/initiate",
        json=payload,
        headers=_HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise Exception(f"Squad initiate failed [{response.status_code}]: {response.text}")

    data = response.json().get("data", {})

    return {
        "transaction_ref": transaction_ref,
        "amount_kobo": amount_kobo,
        "checkout_url": data.get("checkout_url"),
        "customer_email": buyer_email,
        "customer_name": buyer_name,
    }


def verify_payment(transaction_ref: str) -> dict:
    """
    Calls Squad GET /transaction/verify/{ref}.
    Returns the full Squad data dict.
    Raises Exception if the HTTP call itself fails.
    Check data['transaction_status'] == 'Success' for a successful payment.
    """
    response = requests.get(
        f"{SQUAD_BASE_URL}/transaction/verify/{transaction_ref}",
        headers=_HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise Exception(f"Squad verify failed [{response.status_code}]: {response.text}")

    return response.json().get("data", {})