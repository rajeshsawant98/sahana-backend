import asyncio
import re
import os
import threading
import time
from typing import Optional, Tuple

import requests

from app.utils.logger import get_logger

logger = get_logger(__name__)

_geocode_cache: dict[str, Optional[Tuple[float, float]]] = {}
_nominatim_lock = threading.Lock()
_last_nominatim_call = 0.0
_geocode_stats = {
    "cache_hits": 0,
    "provider_requests": 0,
    "provider_successes": 0,
    "provider_failures": 0,
    "skipped_invalid_address": 0,
    "fallback_queries_tried": 0,
    "rate_limited_retries": 0,
}
_INVALID_ADDRESS_TOKENS = {
    "tba",
    "coming soon",
    "online",
    "virtual",
    "to be announced",
    "signup on waitlsit",
    "signup on waitlist",
}
_COUNTRY_ALIASES = {"united states", "usa", "us"}
_US_STATE_CODES = {
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks","ky","la","me","md",
    "ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa","ri","sc",
    "sd","tn","tx","ut","vt","va","wa","wv","wi","wy","dc"
}


def has_valid_coordinates(location: dict) -> bool:
    """True when location has numeric latitude/longitude and is not (0,0)."""
    if not isinstance(location, dict):
        return False

    lat = location.get("latitude")
    lng = location.get("longitude")
    if lat is None or lng is None:
        return False

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return False

    return not (lat_f == 0.0 and lng_f == 0.0)


def _build_address_query(location: dict) -> str:
    formatted = (location.get("formattedAddress") or "").strip()
    city = (location.get("city") or "").strip()
    state = (location.get("state") or "").strip()
    country = (location.get("country") or "United States").strip()

    if formatted and formatted != "N/A":
        parts = [formatted]
        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if country:
            parts.append(country)
        return ", ".join(parts)

    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts)


def _normalize_address_component(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\bPH:\s*\+?\d[\d\s().-]*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bSuite\s+\w+\b", lambda m: m.group(0).replace("  ", " "), value, flags=re.IGNORECASE)
    value = value.strip(" ,")
    lowered = value.lower()
    if lowered in _INVALID_ADDRESS_TOKENS:
        return ""
    return value


def _is_invalid_address_query(address: str) -> bool:
    normalized = address.strip().lower()
    if not normalized:
        return True
    return normalized in _INVALID_ADDRESS_TOKENS


def _dedupe_parts(parts: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        normalized = part.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(part.strip())
    return result


def _clean_formatted_address(formatted: str) -> str:
    value = _normalize_address_component(formatted)
    if not value:
        return ""

    # Drop placeholder lead-ins but keep any actual address content after them.
    value = re.sub(r"^(tba|coming soon|online|virtual|to be announced)\b[\s,:-]*", "", value, flags=re.IGNORECASE)
    value = value.strip(" ,")
    if not value:
        return ""

    value = re.sub(r"\b(tba|coming soon|online|virtual|to be announced)\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip(" ,")

    # Keep only the first sensible address segment when source data has repeated locality chunks.
    parts = [p.strip(" ,") for p in value.split(",") if p.strip(" ,")]
    filtered: list[str] = []
    for part in parts:
        lowered = part.lower()
        if lowered in _INVALID_ADDRESS_TOKENS:
            continue
        if lowered in _COUNTRY_ALIASES:
            continue
        filtered.append(part)

    if not filtered:
        return ""

    # Stop once the string starts repeating city/state/country-like locality info.
    compact: list[str] = []
    for part in filtered:
        lowered = part.lower()
        if compact and lowered == compact[-1].lower():
            continue
        compact.append(part)

    return ", ".join(compact[:3]).strip(" ,")


def _simplify_street_part(value: str) -> str:
    simplified = value
    simplified = re.sub(r",?\s*#\s*[\w-]+", "", simplified, flags=re.IGNORECASE)
    simplified = re.sub(r",?\s*(suite|ste|unit|room|rm|floor|fl)\s*[\w-]+", "", simplified, flags=re.IGNORECASE)
    simplified = re.sub(r",?\s*(ballroom|skyline room|signup on waitlist|waitlist show)\b", "", simplified, flags=re.IGNORECASE)
    simplified = re.sub(r"\s+", " ", simplified).strip(" ,")
    return simplified


def build_address_query(location: dict) -> str:
    if not isinstance(location, dict):
        return ""

    formatted = _clean_formatted_address(location.get("formattedAddress") or "")
    city = _normalize_address_component(location.get("city") or "")
    state = _normalize_address_component(location.get("state") or "")
    country = _normalize_address_component(location.get("country") or "United States")

    locality_parts = _dedupe_parts([city, state])
    if formatted and formatted.upper() != "N/A":
        formatted_lower = formatted.lower()
        parts = [formatted]
        if city and city.lower() not in formatted_lower:
            parts.append(city)
        if state and state.lower() not in formatted_lower:
            parts.append(state)
        if country and country.lower() not in formatted_lower:
            parts.append(country)
        address = ", ".join(_dedupe_parts(parts))
    else:
        address = ", ".join(_dedupe_parts(locality_parts + ([country] if country else [])))

    address = re.sub(r",\s*,+", ", ", address).strip(" ,")
    if _is_invalid_address_query(address):
        return ""
    return address


def _build_address_candidates_with_resolution(location: dict) -> list[tuple[str, str]]:
    if not isinstance(location, dict):
        return []

    formatted = _clean_formatted_address(location.get("formattedAddress") or "")
    city = _normalize_address_component(location.get("city") or "")
    state = _normalize_address_component(location.get("state") or "")
    country = _normalize_address_component(location.get("country") or "United States")

    candidates: list[tuple[str, str]] = []
    primary = build_address_query(location)
    if primary:
        primary_resolution = "street" if formatted else "city"
        candidates.append((primary_resolution, primary))

    simplified_formatted = _simplify_street_part(formatted)
    if simplified_formatted and simplified_formatted != formatted:
        variant_loc = dict(location)
        variant_loc["formattedAddress"] = simplified_formatted
        simplified = build_address_query(variant_loc)
        if simplified and simplified not in [candidate for _, candidate in candidates]:
            candidates.append(("street", simplified))

    city_state_zip = ""
    if formatted:
        zip_match = re.search(r"\b\d{5}(?:-\d{4})?\b", formatted)
        if zip_match and city and state:
            city_state_zip = f"{city}, {state} {zip_match.group(0)}, {country}".strip(" ,")
            city_state_zip = re.sub(r",\s*,+", ", ", city_state_zip)
            if city_state_zip and city_state_zip not in [candidate for _, candidate in candidates]:
                candidates.append(("zip", city_state_zip))

    if city and state:
        city_state = f"{city}, {state}, {country}".strip(" ,")
        city_state = re.sub(r",\s*,+", ", ", city_state)
        if city_state and city_state not in [candidate for _, candidate in candidates]:
            candidates.append(("city", city_state))

    return [(resolution, candidate) for resolution, candidate in candidates if candidate and not _is_invalid_address_query(candidate)]


def build_address_candidates(location: dict) -> list[str]:
    return [candidate for _, candidate in _build_address_candidates_with_resolution(location)]


def get_geocoding_stats() -> dict[str, int]:
    return dict(_geocode_stats)


def resolve_geocoding_provider() -> str:
    provider = (os.getenv("GEOCODING_PROVIDER") or "").strip().lower()
    if provider:
        return provider
    if os.getenv("GEOAPIFY_API_KEY"):
        return "geoapify"
    return "nominatim"


def _is_probably_us_location(address: str) -> bool:
    lowered = (address or "").lower()
    state_matches = re.findall(r",\s*([a-z]{2})(?:\s+\d{5}(?:-\d{4})?)?\s*(?:,|$)", lowered)
    return any(state in _US_STATE_CODES for state in state_matches)


def _geocode_google_sync(address: str, api_key: str) -> Optional[Tuple[float, float]]:
    """Blocking Google geocode call for use via asyncio.to_thread."""
    if address in _geocode_cache:
        _geocode_stats["cache_hits"] += 1
        return _geocode_cache[address]

    _geocode_stats["provider_requests"] += 1
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        logger.info(f"[Geocoding][google] OK address='{address}' status={payload.get('status')}")
    except Exception as e:
        logger.warning(f"Geocoding request failed for '{address}': {e}")
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    status = payload.get("status")
    if status != "OK":
        # Log once per unique address and cache miss as None to avoid repeat calls.
        logger.info(f"Geocoding returned status '{status}' for '{address}'")
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    results = payload.get("results") or []
    if not results:
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    geom = (results[0].get("geometry") or {}).get("location") or {}
    lat = geom.get("lat")
    lng = geom.get("lng")
    try:
        coords = (float(lat), float(lng))
    except (TypeError, ValueError):
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    _geocode_stats["provider_successes"] += 1
    _geocode_cache[address] = coords
    return coords


def _geocode_geoapify_sync(address: str, api_key: str) -> Optional[Tuple[float, float]]:
    """Blocking Geoapify geocode call for use via asyncio.to_thread."""
    if address in _geocode_cache:
        _geocode_stats["cache_hits"] += 1
        return _geocode_cache[address]

    _geocode_stats["provider_requests"] += 1
    try:
        params = {
            "text": address,
            "format": "json",
            "limit": 1,
            "apiKey": api_key,
        }
        if _is_probably_us_location(address):
            params["filter"] = "countrycode:us"
        response = requests.get(
            "https://api.geoapify.com/v1/geocode/search",
            params=params,
            timeout=15,
        )
        if response.status_code == 429:
            logger.warning(f"[Geocoding][geoapify] HTTP 429 for '{address}'")
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logger.warning(f"Geoapify request failed for '{address}': {e}")
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    results = payload.get("results") or []
    if not results:
        logger.info(f"[Geocoding][geoapify] no results for '{address}'")
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    first = results[0]
    lat = first.get("lat")
    lng = first.get("lon")
    try:
        coords = (float(lat), float(lng))
    except (TypeError, ValueError):
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    _geocode_stats["provider_successes"] += 1
    logger.info(f"[Geocoding][geoapify] success for '{address}' -> {coords}")
    _geocode_cache[address] = coords
    return coords


def _nominatim_headers() -> dict:
    user_agent = os.getenv(
        "GEOCODING_USER_AGENT",
        "sahana-backend-geocoder/1.0 (contact: rajesh@sahana.local)",
    )
    return {"User-Agent": user_agent, "Accept-Language": "en-US,en;q=0.8"}


def _geocode_nominatim_sync(address: str) -> Optional[Tuple[float, float]]:
    """
    Blocking OSM Nominatim call. Public instance requires max 1 req/sec and
    a valid User-Agent header.
    """
    global _last_nominatim_call

    if address in _geocode_cache:
        _geocode_stats["cache_hits"] += 1
        return _geocode_cache[address]

    # Respect the Nominatim public usage policy: <= 1 request / second.
    with _nominatim_lock:
        wait = 1.0 - (time.monotonic() - _last_nominatim_call)
        if wait > 0:
            time.sleep(wait)
        _last_nominatim_call = time.monotonic()

    payload = None
    for attempt in range(3):
        _geocode_stats["provider_requests"] += 1
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": address, "format": "jsonv2", "limit": 1},
                headers=_nominatim_headers(),
                timeout=15,
            )
            if response.status_code == 429 and attempt < 2:
                body = response.text[:200].replace("\n", " ")
                retry_after = response.headers.get("Retry-After")
                wait_seconds = 5.0 * (attempt + 1)
                if retry_after:
                    try:
                        parsed_retry_after = float(retry_after)
                        wait_seconds = max(parsed_retry_after, wait_seconds)
                    except (TypeError, ValueError):
                        pass
                _geocode_stats["rate_limited_retries"] += 1
                logger.warning(
                    f"[Geocoding][nominatim] HTTP 429 for '{address}' body='{body}' retrying_in={wait_seconds}s"
                )
                time.sleep(wait_seconds)
                continue
            if response.status_code != 200:
                body = response.text[:200].replace("\n", " ")
                logger.warning(
                    f"[Geocoding][nominatim] HTTP {response.status_code} for '{address}' body='{body}'"
                )
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as e:
            logger.warning(f"Nominatim request failed for '{address}': {e}")
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))
                continue
            _geocode_stats["provider_failures"] += 1
            _geocode_cache[address] = None
            return None

    if payload is None:
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    if not payload:
        logger.info(f"[Geocoding][nominatim] no results for '{address}'")
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    first = payload[0]
    lat = first.get("lat")
    lng = first.get("lon")
    try:
        coords = (float(lat), float(lng))
    except (TypeError, ValueError):
        _geocode_stats["provider_failures"] += 1
        _geocode_cache[address] = None
        return None

    _geocode_stats["provider_successes"] += 1
    logger.info(f"[Geocoding][nominatim] success for '{address}' -> {coords}")
    _geocode_cache[address] = coords
    return coords


async def apply_geocode_fallback(location: dict) -> dict:
    """
    Fill missing/invalid event coordinates using configured geocoder.
    Provider selection:
      - GEOCODING_PROVIDER=nominatim (default, free)
      - GEOCODING_PROVIDER=geoapify (requires GEOAPIFY_API_KEY)
      - GEOCODING_PROVIDER=google (requires GOOGLE_MAPS_API_KEY)
    Returns the updated location dict (or original if no fallback possible).
    """
    if not isinstance(location, dict):
        return location
    if has_valid_coordinates(location):
        return location

    address_candidates = _build_address_candidates_with_resolution(location)
    if not address_candidates:
        _geocode_stats["skipped_invalid_address"] += 1
        return location

    provider = resolve_geocoding_provider()
    coords: Optional[Tuple[float, float]] = None
    resolution_used: Optional[str] = None
    for resolution, address in address_candidates:
        _geocode_stats["fallback_queries_tried"] += 1
        if provider == "google":
            api_key = os.getenv("GOOGLE_MAPS_API_KEY")
            if not api_key:
                return location
            coords = await asyncio.to_thread(_geocode_google_sync, address, api_key)
        elif provider == "geoapify":
            api_key = os.getenv("GEOAPIFY_API_KEY")
            if not api_key:
                return location
            coords = await asyncio.to_thread(_geocode_geoapify_sync, address, api_key)
        else:
            coords = await asyncio.to_thread(_geocode_nominatim_sync, address)
        if coords:
            resolution_used = resolution
            break

    if not coords:
        return location

    lat, lng = coords
    updated = dict(location)
    updated["latitude"] = lat
    updated["longitude"] = lng
    updated["geocodeResolution"] = resolution_used or "unknown"
    updated["geocodeProvider"] = provider
    return updated
