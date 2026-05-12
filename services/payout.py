import os

SQUAD_BASE_URL = os.getenv("SQUAD_BASE_URL", "https://sandbox-api-d.squadco.com")
SQUAD_SECRET_KEY = os.getenv("SQUAD_SECRET_KEY")


def release_funds_to_farmer(
    farmer_account_number: str,
    farmer_bank_code: str,
    farmer_name: str,
    amount_naira: float,
    order_id: str,
) -> dict:
    return {
        "status": "success",
        "message": "Payout recorded (Squad transfer integration pending)",
        "amount": amount_naira,
        "order_id": order_id,
        "farmer": farmer_name,
    }