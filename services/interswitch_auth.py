import os
import requests
from datetime import datetime, timedelta

_cached_token = None
_token_expiry = None


def get_access_token():
    global _cached_token, _token_expiry

    # reuse token if still valid
    if _cached_token and _token_expiry and datetime.utcnow() < _token_expiry:
        return _cached_token

    client_id = os.getenv("INTERSWITCH_CLIENT_ID")
    client_secret = os.getenv("INTERSWITCH_CLIENT_SECRET")
    base_url = os.getenv("INTERSWITCH_BASE_URL")

    if not base_url:
        raise Exception("INTERSWITCH_BASE_URL not set in .env")

    url = f"{base_url}/passport/oauth/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
        "grant_type": "client_credentials"
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers,
        auth=(client_id, client_secret),
    )

    if response.status_code != 200:
        raise Exception(f"OAuth failed: {response.text}")

    data = response.json()

    _cached_token = data["access_token"]
    _token_expiry = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 60)

    print("✅ ACCESS TOKEN GENERATED")
    print(_cached_token)

    return _cached_token