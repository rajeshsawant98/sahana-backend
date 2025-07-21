"""
Location utilities for event ingestion
"""
from app.auth.firebase_init import get_firestore_client
from typing import List, Tuple


def get_unique_user_locations() -> List[Tuple[str, str]]:
    """
    Get unique city/state combinations from user locations in Firestore.
    Used for targeted event ingestion.
    
    Returns:
        List of (city, state) tuples from user profiles
    """
    db = get_firestore_client()
    users_ref = db.collection("users")
    users = users_ref.stream()

    cities = set()
    for user in users:
        data = user.to_dict()
        loc = data.get("location", {})
        if not isinstance(loc, dict):
            print(f"[DEBUG] Unexpected location type: {type(loc)} value: {loc}")
        city = loc.get("city") if isinstance(loc, dict) else None
        state = loc.get("state") if isinstance(loc, dict) else None
        if city and state:
            cities.add((city.strip(), state.strip()))
    return list(cities)
