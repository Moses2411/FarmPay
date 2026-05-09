import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ISW_CLIENT_ID")
CLIENT_SECRET = os.getenv("ISW_CLIENT_SECRET")
BASE_URL = os.getenv("ISW_BASE_URL", "https://qa.interswitchng.com")
PASSPORT_URL = os.getenv(
    "ISW_PASSPORT_URL",
    "https://qa.interswitchng.com/passport/oauth/token",
)
INITIATOR_ID = os.getenv("ISW_INITIATOR_ID", None)
INITIATOR_PASS = os.getenv("ISW_INITIATOR_PASSWORD", None)
IS_SANDBOX = os.getenv("ISW_ENV", "sandbox") == "sandbox"


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


def release_funds_to_farmer(
    farmer_account_number: str,
    farmer_bank_code: str,
    farmer_name: str,
    amount_naira: float,
    order_id: str,
) -> dict:
    amount_kobo = int(amount_naira * 100)
    transfer_code = f"FARMPAY-PAYOUT-{order_id}"

    if IS_SANDBOX and not INITIATOR_ID:
        return {
            "responseCode": "00",
            "responseMessage": "Approved",
            "transferCode": transfer_code,
            "amount": amount_kobo,
            "beneficiaryAccountNumber": farmer_account_number,
            "beneficiaryName": farmer_name,
            "_mock": True,
        }

    token = get_access_token()
    payload = {
        "initiatorId": INITIATOR_ID,
        "initiatorPassword": INITIATOR_PASS,
        "beneficiaryBankCode": farmer_bank_code,
        "beneficiaryAccountNumber": farmer_account_number,
        "beneficiaryName": farmer_name,
        "transferCode": transfer_code,
        "narration": "FarmPay escrow release",
        "amount": amount_kobo,
        "currency": "NGN",
        "senderName": "FarmPay Escrow",
        "senderId": INITIATOR_ID,
        "mac": "",
    }

    response = requests.post(
        f"{BASE_URL}/api/v2/singleTransfer",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()