import hashlib
import base64
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ISW_CLIENT_ID")
CLIENT_SECRET = os.getenv("ISW_CLIENT_SECRET")
MERCHANT_CODE = os.getenv("ISW_MERCHANT_CODE")
PAY_ITEM_ID = os.getenv("ISW_PAY_ITEM_ID")
PASSPORT_URL = os.getenv(
    "ISW_PASSPORT_URL",
    "https://qa.interswitchng.com/passport/oauth/token",
)
BASE_URL = os.getenv("ISW_BASE_URL", "https://qa.interswitchng.com")


def get_access_token() -> str:
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    response = requests.post(
        PASSPORT_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def generate_transaction_ref() -> str:
    return f"FARMPAY-{uuid.uuid4().hex[:12].upper()}"


def generate_hash(transaction_ref: str, amount_kobo: int) -> str:
    raw = f"{MERCHANT_CODE}{PAY_ITEM_ID}{transaction_ref}{amount_kobo}"
    return hashlib.sha512(raw.encode()).hexdigest()


def initiate_payment(
    amount_naira: float,
    buyer_email: str,
    buyer_name: str,
) -> dict:
    amount_kobo = int(amount_naira * 100)
    transaction_ref = generate_transaction_ref()
    hash_value = generate_hash(transaction_ref, amount_kobo)

    return {
        "transaction_ref": transaction_ref,
        "amount_kobo": amount_kobo,
        "hash": hash_value,
        "merchant_code": MERCHANT_CODE,
        "pay_item_id": PAY_ITEM_ID,
        "customer_email": buyer_email,
        "customer_name": buyer_name,
        "currency": 566,
        "mode": "TEST",
    }


def verify_payment(transaction_ref: str, amount_kobo: int) -> dict:
    token = get_access_token()
    hash_value = hashlib.sha512(
        f"{transaction_ref}{amount_kobo}".encode()
    ).hexdigest()

    response = requests.get(
        f"{BASE_URL}/collections/api/v1/gettransaction.json",
        params={
            "merchantcode": MERCHANT_CODE,
            "transactionreference": transaction_ref,
            "amount": amount_kobo,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Hash": hash_value,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()