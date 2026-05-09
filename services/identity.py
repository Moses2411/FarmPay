import requests
import os
from services.interswitch_auth import get_access_token


def get_base_url():
    base_url = os.getenv("INTERSWITCH_BASE_URL")
    if not base_url:
        raise Exception("INTERSWITCH_BASE_URL not set")
    return base_url


def verify_nin(nin: str):
    token = get_access_token()
    base_url = get_base_url()

    url = f"{base_url}/api/v3/purchases"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "requestReference": f"NIN-{nin}",
        "amount": "0",
        "currencyCode": "566",
        "customerId": "test_customer",
        "customerMobile": "08000000000",
        "customerEmail": "test@test.com",
        "paymentDescription": "NIN Verification",
        "payItemId": "VerifyMeNin",   # 🔥 THIS IS THE KEY
        "nameOnCard": "Test User",
        "orderId": "123456",
        "terminalId": "3TLP0001"
    }

    response = requests.post(url, json=payload, headers=headers)

    print("🔍 NIN RESPONSE:", response.status_code, response.text)

    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()


def verify_bank_account(account_number: str, bank_code: str):
    token = get_access_token()
    base_url = get_base_url()

    url = f"{base_url}/api/v3/purchases"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "requestReference": f"ACC-{account_number}",
        "amount": "0",
        "currencyCode": "566",
        "customerId": "test_customer",
        "customerMobile": "08000000000",
        "customerEmail": "test@test.com",
        "paymentDescription": "Account Verification",
        "payItemId": "UVBankVerification",  # 🔥 KEY
        "orderId": "123456",
        "terminalId": "3TLP0001",
        "extraParams": {
            "accountNumber": account_number,
            "bankCode": bank_code
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    print("🏦 BANK RESPONSE:", response.status_code, response.text)

    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()