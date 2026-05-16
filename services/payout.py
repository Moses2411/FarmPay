"""
services/payout.py
Handles: account lookup + fund transfer from Squad wallet to farmer's bank
Based on official Squad documentation
"""

import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_MERCHANT_ID = os.getenv("SQUAD_MERCHANT_ID", "FARMPAY")
IS_SANDBOX = "sandbox" in SQUAD_BASE_URL if SQUAD_BASE_URL else True

_HEADERS = {
    "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
    "Content-Type": "application/json",
}


# Bank codes mapping (from Squad documentation)
BANK_CODES = {
    "sterling bank": "000001",
    "keystone bank": "000002",
    "fcmb": "000003",
    "uba": "000004",
    "fidelity bank": "000007",
    "polaris bank": "000008",
    "ecobank": "000010",
    "unity bank": "000011",
    "stanbic": "000012",
    "gtbank": "000013",
    "access bank": "000014",
    "zenith": "000015",
    "first bank": "000016",
    "wema bank": "000017",
    "union bank": "000018",
    "providus bank": "000023",
    "suntrust bank": "000022",
    "titan trust bank": "000025",
    "globus bank": "000027",
    "lotus bank": "000029",
    "premium trust bank": "000031",
}


def get_bank_code(bank_name: str) -> str:
    """Convert bank name to Squad NIP code"""
    normalized = bank_name.lower().strip()
    for name, code in BANK_CODES.items():
        if name in normalized:
            return code
    return "000014"  # Default to Access Bank


def lookup_account(account_number: str, bank_code: str) -> dict:
    """
    Verify farmer's bank account before transfer.
    Squad requires this step.
    """
    if IS_SANDBOX or not SQUAD_SECRET_KEY:
        return {"account_name": f"Test Farmer", "account_number": account_number}

    response = requests.post(
        f"{SQUAD_BASE_URL}/payout/account/lookup",
        json={"account_number": account_number, "bank_code": bank_code},
        headers=_HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise Exception(f"Account lookup failed: {response.text}")

    data = response.json().get("data", {})
    if not data.get("account_name"):
        raise Exception("Could not resolve account name")

    return data


def requery_transfer(transaction_reference: str) -> dict:
    """
    Re-query transfer status - CRITICAL after receiving 424 timeout
    """
    response = requests.post(
        f"{SQUAD_BASE_URL}/payout/requery",
        json={"transaction_reference": transaction_reference},
        headers=_HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise Exception(f"Re-query failed: {response.text}")

    return response.json()


def release_funds_to_farmer(
    farmer_account_number: str,
    farmer_bank_code: str,
    farmer_name: str,
    amount_naira: float,
    order_id: str,
) -> dict:
    """
    Transfer funds from Squad merchant wallet to farmer's bank account.
    Amount is in Naira (converted to Kobo for API)
    """
    amount_kobo = int(amount_naira * 100)
    transaction_reference = f"{SQUAD_MERCHANT_ID}_{order_id[:20]}"

    # Sandbox mock mode
    if IS_SANDBOX or not SQUAD_SECRET_KEY:
        logger.info(f"[SANDBOX MOCK] Releasing ₦{amount_naira:,.2f} to {farmer_account_number}")
        return {
            "success": True,
            "message": "Mock payout - sandbox mode",
            "transaction_reference": transaction_reference,
            "amount_kobo": amount_kobo,
            "mock": True,
        }

    # Step 1: Lookup account
    try:
        account_info = lookup_account(farmer_account_number, farmer_bank_code)
        resolved_name = account_info.get("account_name", farmer_name)
    except Exception as e:
        raise Exception(f"Account verification failed: {str(e)}")

    # Step 2: Transfer (amount in Kobo as string)
    payload = {
        "transaction_reference": transaction_reference,
        "amount": str(amount_kobo),  # Must be string in Kobo
        "bank_code": farmer_bank_code,
        "account_number": farmer_account_number,
        "account_name": resolved_name,
        "currency_id": "NGN",
        "remark": f"FarmPay order {order_id} escrow release",
    }

    response = requests.post(
        f"{SQUAD_BASE_URL}/payout/transfer",
        json=payload,
        headers=_HEADERS,
        timeout=20,
    )

    # Handle 424 timeout - re-query before retrying
    if response.status_code == 424:
        status = requery_transfer(transaction_reference)
        if status.get("data", {}).get("response_description") in ("Approved or completed successfully", "Transaction Success"):
            return status
        raise Exception(f"Transfer timed out (424) - re-query shows: {status}")

    if response.status_code not in (200, 201):
        raise Exception(f"Transfer failed: {response.text}")

    return response.json()