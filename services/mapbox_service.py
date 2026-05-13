import os
import requests
from dotenv import load_dotenv

load_dotenv()

MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
BASE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving"

RATE_PER_KM = 1200  # Naira per kilometer


def get_distance_km(origin: str, destination: str) -> float:
    """
    Calculate driving distance between two locations.
    origin/destination: "longitude,latitude" format or place names
    Returns: distance in kilometers
    """
    if not MAPBOX_ACCESS_TOKEN:
        return _estimate_default(origin, destination)

    try:
        url = f"{BASE_URL}/{origin};{destination}"
        params = {
            "access_token": MAPBOX_ACCESS_TOKEN,
            "geometries": "distance",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        routes = data.get("routes", [])

        if routes:
            distance_meters = routes[0].get("distance", 0)
            return round(distance_meters / 1000, 2)

    except Exception as e:
        print(f"Mapbox error: {e}")

    return _estimate_default(origin, destination)


def _estimate_default(origin: str, destination: str) -> float:
    """Fallback: estimate 5km if no API key configured."""
    return 5.0


def calculate_delivery_fee(origin: str, destination: str) -> dict:
    """
    Calculate delivery fee based on distance.
    Returns distance in km and delivery fee in naira.
    """
    distance_km = get_distance_km(origin, destination)

    if distance_km <= 2:
        delivery_fee = 1000
    else:
        delivery_fee = int(distance_km * RATE_PER_KM)

    return {
        "distance_km": distance_km,
        "delivery_fee": delivery_fee,
        "rate_per_km": RATE_PER_KM,
    }


def geocode_address(address: str) -> tuple[float, float]:
    """
    Convert address string to coordinates.
    Returns: (longitude, latitude)
    """
    if not MAPBOX_ACCESS_TOKEN:
        return None, None

    try:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json"
        params = {
            "access_token": MAPBOX_ACCESS_TOKEN,
            "limit": 1,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        if features:
            coords = features[0]["center"]
            return coords[0], coords[1]

    except Exception as e:
        print(f"Geocoding error: {e}")

    return None, None