import asyncio

from app.utils import geocoding


def test_has_valid_coordinates():
    assert geocoding.has_valid_coordinates({"latitude": 33.4, "longitude": -112.0}) is True
    assert geocoding.has_valid_coordinates({"latitude": 0.0, "longitude": 0.0}) is False
    assert geocoding.has_valid_coordinates({"latitude": None, "longitude": -112.0}) is False
    assert geocoding.has_valid_coordinates({}) is False


def test_build_address_query_filters_invalid_placeholder():
    location = {
        "formattedAddress": "TBA",
        "city": "Phoenix",
        "state": "AZ",
        "country": "United States",
    }
    assert geocoding.build_address_query(location) == "Phoenix, AZ, United States"


def test_build_address_query_strips_phone_noise():
    location = {
        "formattedAddress": "16165 North 83rd Avenue Suite 200 PH: +1 469 666 9332",
        "city": "Peoria",
        "state": "AZ",
        "country": "United States",
    }
    result = geocoding.build_address_query(location)
    assert "469 666 9332" not in result
    assert "Peoria" in result


def test_build_address_query_removes_duplicate_locality():
    location = {
        "formattedAddress": "2301 N Central Ave, Phoenix, AZ 85004, United States",
        "city": "Phoenix",
        "state": "AZ",
        "country": "United States",
    }
    assert geocoding.build_address_query(location) == "2301 N Central Ave, Phoenix, AZ 85004, United States"


def test_build_address_query_strips_placeholder_prefix():
    location = {
        "formattedAddress": "TBA, Dallas, TX 75001",
        "city": "Dallas",
        "state": "TX",
        "country": "United States",
    }
    assert geocoding.build_address_query(location) == "Dallas, TX 75001, United States"


def test_build_address_candidates_adds_simplified_forms():
    location = {
        "formattedAddress": "310 East Abram Street, #150",
        "city": "Arlington",
        "state": "TX",
        "country": "United States",
    }
    candidates = geocoding.build_address_candidates(location)
    assert "310 East Abram Street, #150, Arlington, TX, United States" in candidates
    assert "310 East Abram Street, Arlington, TX, United States" in candidates
    assert "Arlington, TX, United States" in candidates


def test_build_address_candidates_uses_city_state_zip_fallback():
    location = {
        "formattedAddress": "TBA, Dallas, TX 75001",
        "city": "Dallas",
        "state": "TX",
        "country": "United States",
    }
    candidates = geocoding.build_address_candidates(location)
    assert candidates[0] == "Dallas, TX 75001, United States"
    assert "Dallas, TX, United States" in candidates


def test_geoapify_us_heuristic_accepts_us_address():
    assert geocoding._is_probably_us_location("Phoenix, AZ 85004, United States") is True


def test_geoapify_us_heuristic_rejects_non_us_address():
    assert geocoding._is_probably_us_location("shenzhen, shenzhen 123456, United States") is False


def test_apply_geocode_fallback_no_api_key(monkeypatch):
    monkeypatch.setenv("GEOCODING_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    location = {"city": "Phoenix", "state": "AZ", "country": "United States"}

    updated = asyncio.run(geocoding.apply_geocode_fallback(location))
    assert updated == location


def test_apply_geocode_fallback_no_geoapify_api_key(monkeypatch):
    monkeypatch.setenv("GEOCODING_PROVIDER", "geoapify")
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    location = {"city": "Phoenix", "state": "AZ", "country": "United States"}

    updated = asyncio.run(geocoding.apply_geocode_fallback(location))
    assert updated == location


def test_apply_geocode_fallback_google_success(monkeypatch):
    monkeypatch.setenv("GEOCODING_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "dummy-key")

    # Reset module cache for deterministic test behavior.
    geocoding._geocode_cache.clear()

    def fake_geocode(address: str, api_key: str):
        assert "Phoenix" in address
        assert api_key == "dummy-key"
        return (33.4484, -112.0740)

    monkeypatch.setattr(geocoding, "_geocode_google_sync", fake_geocode)

    location = {
        "formattedAddress": "123 Main St",
        "city": "Phoenix",
        "state": "AZ",
        "country": "United States",
        "latitude": 0.0,
        "longitude": 0.0,
    }
    updated = asyncio.run(geocoding.apply_geocode_fallback(location))

    assert updated["latitude"] == 33.4484
    assert updated["longitude"] == -112.074
    assert updated["geocodeResolution"] == "street"
    assert updated["geocodeProvider"] == "google"


def test_apply_geocode_fallback_nominatim_success(monkeypatch):
    monkeypatch.setenv("GEOCODING_PROVIDER", "nominatim")
    geocoding._geocode_cache.clear()

    def fake_geocode(address: str):
        assert "Phoenix" in address
        return (33.4484, -112.0740)

    monkeypatch.setattr(geocoding, "_geocode_nominatim_sync", fake_geocode)

    location = {
        "formattedAddress": "123 Main St",
        "city": "Phoenix",
        "state": "AZ",
        "country": "United States",
        "latitude": 0.0,
        "longitude": 0.0,
    }
    updated = asyncio.run(geocoding.apply_geocode_fallback(location))

    assert updated["latitude"] == 33.4484
    assert updated["longitude"] == -112.074
    assert updated["geocodeResolution"] == "street"
    assert updated["geocodeProvider"] == "nominatim"


def test_apply_geocode_fallback_geoapify_success(monkeypatch):
    monkeypatch.setenv("GEOCODING_PROVIDER", "geoapify")
    monkeypatch.setenv("GEOAPIFY_API_KEY", "dummy-key")
    geocoding._geocode_cache.clear()

    def fake_geocode(address: str, api_key: str):
        assert "Phoenix" in address
        assert api_key == "dummy-key"
        return (33.4484, -112.0740)

    monkeypatch.setattr(geocoding, "_geocode_geoapify_sync", fake_geocode)

    location = {
        "formattedAddress": "123 Main St",
        "city": "Phoenix",
        "state": "AZ",
        "country": "United States",
        "latitude": 0.0,
        "longitude": 0.0,
    }
    updated = asyncio.run(geocoding.apply_geocode_fallback(location))

    assert updated["latitude"] == 33.4484
    assert updated["longitude"] == -112.074
    assert updated["geocodeResolution"] == "street"
    assert updated["geocodeProvider"] == "geoapify"
