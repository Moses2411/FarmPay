import uuid
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY")
SQUAD_PUBLIC_KEY = os.getenv("SQUAD_PUBLIC_KEY")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_CALLBACK_URL = os.getenv("SQUAD_CALLBACK_URL")


def generate_transaction_ref() -> str:
    return f"FARMPAY-{uuid.uuid4().hex[:12].upper()}"


def initiate_payment(
    amount_kobo: int,
    buyer_email: str,
    buyer_name: str,
    transaction_ref: str = None,
    payment_channels: list = None,
) -> dict:
    if transaction_ref is None:
        transaction_ref = generate_transaction_ref()

    if payment_channels is None:
        payment_channels = ["card", "bank", "ussd", "transfer"]

    headers = {
        "Authorization": SQUAD_SECRET_KEY,
        "Content-Type": "application/json",
    }

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
        headers=headers,
        timeout=15,
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
        "transaction_amount": data["data"]["transaction_amount"],
        "authorized_channels": data["data"]["authorized_channels"],
        "currency": data["data"]["currency"],
        "merchant_id": data["data"]["merchant_info"]["merchant_id"],
    }


def verify_payment(transaction_ref: str) -> dict:
    headers = {
        "Authorization": SQUAD_SECRET_KEY,
    }

    response = requests.get(
        f"{SQUAD_BASE_URL}/transaction/verify/{transaction_ref}",
        headers=headers,
        timeout=15,
    )

    if response.status_code == 400:
        return {"valid": False, "error": "Invalid transaction reference"}
    elif response.status_code == 401:
        raise Exception("Squad API: Unauthorized")
    elif response.status_code == 403:
        raise Exception("Squad API: Forbidden - Invalid API key")

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


def simulate_transfer_payment(virtual_account_number: str, amount: int) -> dict:
    headers = {
        "Authorization": SQUAD_SECRET_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "virtual_account_number": virtual_account_number,
        "amount": amount,
    }

    response = requests.post(
        f"{SQUAD_BASE_URL}/virtual-account/simulate/payment",
        json=payload,
        headers=headers,
        timeout=15,
    )

    data = response.json()

    if data.get("success"):
        return {"success": True, "message": data.get("message")}
    else:
        raise Exception(f"Simulation failed: {data.get('message')}")