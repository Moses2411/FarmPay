# services/identity.py
import requests
import os
# from services.interswitch_auth import get_access_token  # REMOVE THIS - migrating to Squadco


def get_base_url():
    base_url = os.getenv("INTERSWITCH_BASE_URL")
    if not base_url:
        # Return mock URL for now since we're migrating
        return "https://mock-api.example.com"
    return base_url


def verify_nin(nin: str):
    """
    TODO: Migrate NIN verification to Squadco or alternative provider
    For now, return mock success for testing
    """
    # Mock response for testing
    return {
        "status": "success",
        "nin": nin,
        "name": "Test User",
        "verified": True
    }
    
    # Original Interswitch code (commented out)
    # token = get_access_token()
    # base_url = get_base_url()
    # url = f"{base_url}/api/v3/purchases"
    # ... etc


def verify_bank_account(account_number: str, bank_code: str):
    """
    TODO: Migrate bank verification to Squadco or alternative provider
    For now, return mock success for testing
    """
    # Mock response for testing
    return {
        "status": "success",
        "account_number": account_number,
        "account_name": "Test Farmer",
        "bank_code": bank_code,
        "verified": True
    }
    
    # Original Interswitch code (commented out)
    # token = get_access_token()
    # base_url = get_base_url()
    # url = f"{base_url}/api/v3/purchases"
    # ... etc