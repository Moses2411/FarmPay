"""
services/payout.py
Squad Co Transfer API — replaces Interswitch payout service.
Handles: account name lookup + fund transfer to farmer bank account.

Important Squad rules:
  - Always lookup account name before transferring.
  - transaction_reference MUST be prefixed with your Squad Merchant ID.
    Set SQUAD_MERCHANT_ID in .env (found on your Squad dashboard).
  - Amount is in KOBO.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_MERCHANT_ID = os.getenv("SQUAD_MERCHANT_ID", "FARMPAY")   # replace with real ID from dashboard
IS_SANDBOX = "sandbox" in SQUAD_BASE_URL

_HEADERS = {
    "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
    "Content-Type": "application/json",
}


def lookup_account(account_number: str, bank_code: str) -> str:
    """
    Verifies the farmer's bank account and returns the account name.
    Squad requires this step before any transfer.
    Raises Exception on failure.
    """
    response = requests.post(
        f"{SQUAD_BASE_URL}/payout/account/lookup",
        json={"account_number": account_number, "bank_code": bank_code},
        headers=_HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise Exception(
            f"Account lookup failed [{response.status_code}]: {response.text}"
        )

    data = response.json().get("data", {})
    account_name = data.get("account_name")
    if not account_name:
        raise Exception("Could not resolve account name from Squad lookup")

    return account_name


def release_funds_to_farmer(
    farmer_account_number: str,
    farmer_bank_code: str,
    farmer_name: str,          # used as fallback; lookup overrides this
    amount_naira: float,
    order_id: str,
) -> dict:
    """
    Transfers escrow funds from Squad Wallet to the farmer's bank account.

    In sandbox mode without a funded wallet, returns a mock success so the
    rest of the order flow (delivery confirmation, escrow release) still works.

    In production, set IS_SANDBOX=false (SQUAD_BASE_URL without 'sandbox').
    """
    amount_kobo = int(amount_naira * 100)

    # Squad requires merchant ID prefix on transaction reference
    transaction_reference = f"{SQUAD_MERCHANT_ID}_{order_id[:20]}"

    # ── Sandbox mock (no wallet needed for dev/testing) ──────────────────
    if IS_SANDBOX:
        print(f"[SQUAD MOCK PAYOUT] ₦{amount_naira:,.2f} → {farmer_account_number} | ref: {transaction_reference}")
        return {
            "success": True,
            "message": "Mock payout approved (sandbox — no wallet deducted)",
            "transaction_reference": transaction_reference,
            "amount_kobo": amount_kobo,
            "beneficiary_account": farmer_account_number,
            "beneficiary_name": farmer_name,
            "_mock": True,
        }

    # ── Production: lookup first, then transfer ───────────────────────────
    try:
        resolved_name = lookup_account(farmer_account_number, farmer_bank_code)
    except Exception as e:
        raise Exception(f"Pre-transfer account lookup failed: {str(e)}")

    payload = {
        "transaction_reference": transaction_reference,
        "amount": str(amount_kobo),           # Squad expects string for amount
        "bank_code": farmer_bank_code,
        "account_number": farmer_account_number,
        "account_name": resolved_name,
        "currency_id": "NGN",
        "remark": f"FarmPay escrow release — order {order_id}",
    }

    response = requests.post(
        f"{SQUAD_BASE_URL}/payout/transfer",
        json=payload,
        headers=_HEADERS,
        timeout=20,
    )

    # 424 = timeout/failed — squad recommends re-querying, not treating as error
    if response.status_code == 424:
        raise Exception(
            f"Transfer timed out (424). Re-query ref {transaction_reference} before retrying."
        )

    if response.status_code not in (200, 201):
        raise Exception(
            f"Squad transfer failed [{response.status_code}]: {response.text}"
        )

    return response.json()