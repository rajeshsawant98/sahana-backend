"""
Tests for the nearby events cursor-pagination endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.pagination import EventCursorPaginatedResponse

client = TestClient(app)

MOCK_EVENT = {
    "eventId": "evt-001",
    "eventName": "Phoenicians ft. Lemon Squeezy",
    "startTime": "2026-04-01T19:00:00+00:00",
    "location": {"city": "Phoenix", "state": "AZ"},
    "isArchived": False,
}


def _nearby_response(items, has_next=False, next_cursor=None, page_size=10):
    return EventCursorPaginatedResponse.create(
        items=items,
        next_cursor=next_cursor,
        prev_cursor=None,
        has_next=has_next,
        has_previous=False,
        page_size=page_size,
    )


def test_nearby_events_returns_cursor_shape():
    """Nearby events endpoint returns cursor-paginated shape, not offset shape."""
    with patch(
        "app.routes.event_routes.get_nearby_events_paginated",
        new_callable=AsyncMock,
        return_value=_nearby_response([MOCK_EVENT]),
    ):
        response = client.get(
            "/api/events/location/nearby?city=Phoenix&state=AZ&page_size=10"
        )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert "has_next" in data["pagination"]
    assert "has_previous" in data["pagination"]
    assert "next_cursor" in data["pagination"]
    # Old offset fields absent
    assert "total_count" not in data
    assert "page" not in data
    assert "total_pages" not in data


def test_nearby_events_returns_events_in_items():
    """Events are nested under 'items'."""
    with patch(
        "app.routes.event_routes.get_nearby_events_paginated",
        new_callable=AsyncMock,
        return_value=_nearby_response([MOCK_EVENT]),
    ):
        response = client.get(
            "/api/events/location/nearby?city=Phoenix&state=AZ&page_size=10"
        )

    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["eventName"] == "Phoenicians ft. Lemon Squeezy"


def test_nearby_events_has_next_when_more_results():
    """has_next is True when there is a next page."""
    with patch(
        "app.routes.event_routes.get_nearby_events_paginated",
        new_callable=AsyncMock,
        return_value=_nearby_response([MOCK_EVENT], has_next=True, next_cursor="next-token"),
    ):
        response = client.get(
            "/api/events/location/nearby?city=Phoenix&state=AZ&page_size=1"
        )

    data = response.json()
    assert data["pagination"]["has_next"] is True
    assert data["pagination"]["next_cursor"] is not None


def test_nearby_events_page_size_respected():
    """page_size in response matches the requested page_size."""
    with patch(
        "app.routes.event_routes.get_nearby_events_paginated",
        new_callable=AsyncMock,
        return_value=_nearby_response([], page_size=3),
    ):
        response = client.get(
            "/api/events/location/nearby?city=Phoenix&state=AZ&page_size=3"
        )

    assert response.json()["pagination"]["page_size"] == 3


def test_nearby_events_empty_city_returns_results():
    """An empty city still returns a valid cursor-paginated response."""
    with patch(
        "app.routes.event_routes.get_nearby_events_paginated",
        new_callable=AsyncMock,
        return_value=_nearby_response([]),
    ):
        response = client.get(
            "/api/events/location/nearby?city=Smalltown&state=AZ&page_size=10"
        )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["pagination"]["has_next"] is False
