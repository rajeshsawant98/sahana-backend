"""
Integration test for pagination API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_events_paginated_endpoint():
    """Test the events endpoint with pagination enabled"""
    response = client.get("/api/events?page=1&page_size=5")
    assert response.status_code == 200
    
    data = response.json()
    # Check pagination structure
    assert "items" in data
    assert "total_count" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert "has_next" in data
    assert "has_previous" in data
    
    # Check pagination values
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["has_previous"] is False


def test_events_non_paginated():
    """Test the events endpoint without pagination (legacy behavior)"""
    response = client.get("/api/events")
    assert response.status_code == 200
    
    data = response.json()
    # Should have legacy structure
    assert "events" in data
    # Should NOT have pagination metadata
    assert "total_count" not in data
    assert "page" not in data


def test_events_paginated_with_filters():
    """Test the events endpoint with pagination and filters"""
    response = client.get("/api/events?page=1&page_size=10&is_online=true")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_events_paginated_invalid_params():
    """Test the events endpoint with invalid pagination parameters"""
    # Test invalid page (too small)
    response = client.get("/api/events?page=0&page_size=10")
    assert response.status_code == 422  # Validation error
    
    # Test invalid page_size (too large)
    response = client.get("/api/events?page=1&page_size=101")
    assert response.status_code == 422  # Validation error


def test_nearby_events_paginated_endpoint():
    """Test the nearby events endpoint with pagination"""
    response = client.get("/api/events/location/nearby?city=Austin&state=Texas&page=1&page_size=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total_count" in data
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_nearby_events_non_paginated():
    """Test the nearby events endpoint without pagination"""
    response = client.get("/api/events/location/nearby?city=Austin&state=Texas")
    assert response.status_code == 200
    
    data = response.json()
    assert "events" in data
    assert "count" in data
    # Should NOT have pagination metadata
    assert "total_count" not in data


def test_nearby_events_paginated_missing_params():
    """Test the nearby events endpoint with missing required parameters"""
    response = client.get("/api/events/location/nearby?page=1&page_size=5")
    assert response.status_code == 422  # Missing city and state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
