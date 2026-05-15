"""
services/virtual_account.py
Manages Squad Static Virtual Accounts for farmers (B2B endpoint)
"""

import os
import requests
import logging
from typing import Dict
from sqlalchemy.orm import Session

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY")
SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")

_HEADERS = {
    "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
    "Content-Type": "application/json",
}


class SquadVirtualAccountService:
    """Handles Static Virtual Accounts for farmers using B2B endpoint"""

    def __init__(self, db: Session):
        self.db = db

    def create_farmer_virtual_account(
        self,
        farmer_id: str,
        business_name: str,
        mobile_number: str,
        bvn: str,
        beneficiary_account: str,
    ) -> Dict:
        """
        Create a static virtual account for a farmer.
        beneficiary_account is the farmer's bank account (where money will go when released).
        Uses POST /virtual-account/business endpoint.
        """
        # Validate BVN (must be 11 digits)
        bvn = str(bvn).strip()
        if len(bvn) != 11:
            raise Exception(f"BVN must be 11 digits, got {len(bvn)} digits")

        # Ensure business_name has at least 2 words
        if len(business_name.split()) < 2:
            business_name = f"{business_name} Farm"

        customer_identifier = f"FARMER_{farmer_id[:20]}"

        payload = {
            "customer_identifier": customer_identifier,
            "business_name": business_name[:50],
            "mobile_num": mobile_number,
            "bvn": bvn,
            "beneficiary_account": beneficiary_account,
        }

        logger.info(f"Creating VA for {business_name}")
        logger.debug(f"Payload: {payload}")

        try:
            response = requests.post(
                f"{SQUAD_BASE_URL}/virtual-account/business",
                json=payload,
                headers=_HEADERS,
                timeout=30,
            )

            logger.info(f"Response status: {response.status_code}")

            if response.status_code != 200:
                error_msg = f"VA creation failed: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()
            data = result.get("data", {})

            logger.info(f"✅ VA created: {data.get('virtual_account_number')}")

            return {
                "success": True,
                "account_number": data.get("virtual_account_number"),
                "account_name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                "bank_code": data.get("bank_code"),
                "bank_name": "GTBank",
                "customer_identifier": customer_identifier,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise Exception(f"Failed to connect to Squad: {str(e)}")

    def get_virtual_account(self, customer_identifier: str) -> Dict:
        """Get virtual account details for a customer"""
        try:
            response = requests.get(
                f"{SQUAD_BASE_URL}/virtual-account/business/{customer_identifier}",
                headers=_HEADERS,
                timeout=30,
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get VA: {response.text}")

            return response.json().get("data", {})

        except Exception as e:
            logger.error(f"Error getting VA: {str(e)}")
            return {}