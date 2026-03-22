"""
Integration tests for cursor-paginated API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def _mock_cursor_response(items=None, has_next=False, has_previous=False):
    return {
        "items": items or [],
        "next_cursor": None,
        "prev_cursor": None,
        "has_next": has_next,
        "has_previous": has_previous,
        "page_size": 5,
    }


# ── /api/events ────────────────────────────────────────────────────────────────

def test_events_paginated_endpoint():
    """Cursor-paginated events endpoint returns correct shape."""
    with patch(
        "app.routes.event_routes.get_all_events_paginated",
        new_callable=AsyncMock,
        return_value=_mock_cursor_response(),
    ):
        response = client.get("/api/events?page_size=5")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "next_cursor" in data
    assert "has_next" in data
    assert "has_previous" in data
    assert "page_size" in data
    # Old offset fields must NOT be present
    assert "total_count" not in data
    assert "page" not in data
    assert "total_pages" not in data


def test_events_returns_items_list():
    """items is a list (even when empty)."""
    with patch(
        "app.routes.event_routes.get_all_events_paginated",
        new_callable=AsyncMock,
        return_value=_mock_cursor_response(),
    ):
        response = client.get("/api/events")

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_events_paginated_with_filters():
    """Filters are accepted without error."""
    with patch(
        "app.routes.event_routes.get_all_events_paginated",
        new_callable=AsyncMock,
        return_value=_mock_cursor_response(),
    ):
        response = client.get("/api/events?page_size=10&is_online=true")

    assert response.status_code == 200
    assert "items" in response.json()


def test_events_paginated_invalid_page_size_too_large():
    """page_size > 100 is rejected with 422."""
    response = client.get("/api/events?page_size=101")
    assert response.status_code == 422


def test_events_next_cursor_propagated():
    """next_cursor from service is returned to client."""
    with patch(
        "app.routes.event_routes.get_all_events_paginated",
        new_callable=AsyncMock,
        return_value={
            "items": [{"eventId": "abc"}],
            "next_cursor": "cursor-token-xyz",
            "prev_cursor": None,
            "has_next": True,
            "has_previous": False,
            "page_size": 1,
        },
    ):
        response = client.get("/api/events?page_size=1")

    assert response.status_code == 200
    assert response.json()["next_cursor"] == "cursor-token-xyz"
    assert response.json()["has_next"] is True


# ── /api/events/location/nearby ────────────────────────────────────────────────

def test_nearby_events_paginated_endpoint():
    """Nearby events returns cursor-paginated shape."""
    with patch(
        "app.routes.event_routes.get_nearby_events_paginated",
        new_callable=AsyncMock,
        return_value=_mock_cursor_response(),
    ):
        response = client.get("/api/events/location/nearby?city=Austin&state=TX&page_size=5")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "has_next" in data
    assert "total_count" not in data


def test_nearby_events_missing_city_returns_422():
    """city and state are required query params."""
    response = client.get("/api/events/location/nearby?page_size=5")
    assert response.status_code == 422


def test_nearby_events_missing_state_returns_422():
    response = client.get("/api/events/location/nearby?city=Austin&page_size=5")
    assert response.status_code == 422
