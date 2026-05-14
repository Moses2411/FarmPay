"""
services/payout.py
Squad Transfer API — account lookup, fund transfer, re-query.
This is what actually moves escrow money from your Squad wallet to the farmer's bank.
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY", "")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_MERCHANT_ID = os.getenv("SQUAD_MERCHANT_ID", "FARMPAY")
IS_SANDBOX = "sandbox" in SQUAD_BASE_URL.lower()

_HEADERS = {
    "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
    "Content-Type": "application/json",
}


def lookup_account(account_number: str, bank_code: str) -> dict:
    """
    Verify farmer's bank account before any transfer.
    Squad requires this step — never skip it in production.
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
        raise Exception("Could not resolve account name from Squad lookup response")

    return data


def requery_transfer(transaction_reference: str) -> dict:
    """
    Re-query transfer status after a 424 timeout.
    Per Squad docs: always re-query before deciding to retry.
    """
    response = requests.post(
        f"{SQUAD_BASE_URL}/payout/requery",
        json={"transaction_reference": transaction_reference},
        headers=_HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise Exception(
            f"Re-query failed [{response.status_code}]: {response.text}"
        )

    return response.json()


def release_funds_to_farmer(
    farmer_account_number: str,
    farmer_bank_code: str,
    farmer_name: str,
    amount_naira: float,
    order_id: str,
) -> dict:
    """
    Transfer escrow funds from your Squad merchant wallet to the farmer's bank.

    Flow:
      1. Sandbox → return mock response immediately (no wallet needed).
      2. Production → account lookup → transfer → handle 424 timeout.

    Returns a dict with at minimum:
      { success: bool, transaction_reference: str, payout_status: str }
    """
    amount_kobo = int(round(amount_naira * 100))
    transaction_reference = f"{SQUAD_MERCHANT_ID}_{order_id[:20]}"

    # ── Sandbox mock ─────────────────────────────────────────────────────
    if IS_SANDBOX or not SQUAD_SECRET_KEY:
        logger.info(
            f"[SQUAD MOCK PAYOUT] ₦{amount_naira:,.2f} → {farmer_account_number} "
            f"| ref: {transaction_reference}"
        )
        return {
            "success": True,
            "message": "Mock payout approved (sandbox)",
            "transaction_reference": transaction_reference,
            "amount_kobo": amount_kobo,
            "beneficiary_account": farmer_account_number,
            "beneficiary_name": farmer_name,
            "payout_status": "success",
            "_mock": True,
        }

    # ── Production ───────────────────────────────────────────────────────
    # Step 1: account lookup
    try:
        account_info = lookup_account(farmer_account_number, farmer_bank_code)
        resolved_name = account_info.get("account_name", farmer_name)
    except Exception as e:
        raise Exception(f"Pre-transfer account lookup failed: {str(e)}")

    # Step 2: transfer
    payload = {
        "transaction_reference": transaction_reference,
        "amount": str(amount_kobo),
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

    # Step 3: handle 424 timeout — re-query, do NOT blindly retry
    if response.status_code == 424:
        logger.warning(
            f"[SQUAD] 424 timeout for {transaction_reference} — re-querying"
        )
        try:
            requery_result = requery_transfer(transaction_reference)
            status = requery_result.get("data", {}).get("status", "").upper()
            if status == "SUCCESS":
                return {
                    "success": True,
                    "transaction_reference": transaction_reference,
                    "payout_status": "success",
                    "message": "Transfer confirmed via re-query after 424",
                    "_requeried": True,
                }
            raise Exception(
                f"Transfer timed out (424). Re-query status: {status}. "
                f"Full response: {requery_result}"
            )
        except Exception as e:
            raise Exception(f"424 timeout and re-query failed: {str(e)}")

    if response.status_code == 200:
        # Squad returns 200 for already-existing reference too — check status
        data = response.json()
        return {
            "success": True,
            "transaction_reference": transaction_reference,
            "payout_status": "success",
            "message": data.get("message", "Transfer initiated"),
            "raw": data,
        }

    raise Exception(
        f"Squad transfer failed [{response.status_code}]: {response.text}"
    )