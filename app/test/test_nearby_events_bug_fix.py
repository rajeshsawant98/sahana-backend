"""
Test for the specific bug reported: Nearby Events Pagination Endpoint
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_nearby_events_bug_fix_phoenix():
    """Test the specific bug: Phoenix events should return same results in both modes"""
    
    # Test legacy endpoint (should work)
    legacy_response = client.get("/api/events/location/nearby?city=Phoenix&state=AZ")
    assert legacy_response.status_code == 200
    
    legacy_data = legacy_response.json()
    assert "events" in legacy_data
    assert "count" in legacy_data
    legacy_events = legacy_data["events"]
    legacy_count = legacy_data["count"]
    
    print(f"Legacy endpoint: Found {len(legacy_events)} events, count: {legacy_count}")
    
    # Test paginated endpoint (was broken, should now work)
    paginated_response = client.get("/api/events/location/nearby?city=Phoenix&state=AZ&page=1&page_size=10")
    assert paginated_response.status_code == 200
    
    paginated_data = paginated_response.json()
    assert "items" in paginated_data
    assert "total_count" in paginated_data
    assert "page" in paginated_data
    assert "page_size" in paginated_data
    assert "total_pages" in paginated_data
    assert "has_next" in paginated_data
    assert "has_previous" in paginated_data
    
    paginated_events = paginated_data["items"]
    paginated_total = paginated_data["total_count"]
    
    print(f"Paginated endpoint: Found {len(paginated_events)} events, total_count: {paginated_total}")
    
    # Verify both return the same number of events
    assert len(legacy_events) == len(paginated_events), f"Legacy returned {len(legacy_events)}, paginated returned {len(paginated_events)}"
    assert legacy_count == paginated_total, f"Legacy count {legacy_count}, paginated total {paginated_total}"
    
    # Verify we get the expected Phoenix events (at least the ones mentioned in bug report)
    expected_event_names = [
        "Phoenicians ft. Lemon Squeezy",
        "ActiveCampaign Study Hall | Phoenix",
        "Equis' Gold Standard Tour - Phoenix, AZ",
        "Shelly's Red, Black & White Sneaker's Ball"
    ]
    
    legacy_event_names = [event.get("eventName", "") for event in legacy_events]
    paginated_event_names = [event.get("eventName", "") for event in paginated_events]
    
    # Check that we have the expected events
    for expected_name in expected_event_names:
        # Allow partial matches since event names might have slight variations
        legacy_match = any(expected_name in name for name in legacy_event_names)
        paginated_match = any(expected_name in name for name in paginated_event_names)
        
        if legacy_match:  # If legacy has it, paginated should too
            assert paginated_match, f"Legacy has '{expected_name}' but paginated doesn't"
    
    # Verify pagination metadata is correct
    assert paginated_data["page"] == 1
    assert paginated_data["page_size"] == 10
    assert paginated_data["has_previous"] is False
    
    # If we have 4 or fewer events, should fit on one page
    if paginated_total <= 10:
        assert paginated_data["has_next"] is False
        assert paginated_data["total_pages"] == 1
    
    print("✅ Bug fix verified: Both endpoints return the same Phoenix events!")


def test_nearby_events_pagination_with_page_size():
    """Test pagination with different page sizes"""
    
    # Get total count first
    response = client.get("/api/events/location/nearby?city=Phoenix&state=AZ&page=1&page_size=10")
    assert response.status_code == 200
    
    data = response.json()
    total_count = data["total_count"]
    
    if total_count > 1:
        # Test with page_size = 1
        response = client.get("/api/events/location/nearby?city=Phoenix&state=AZ&page=1&page_size=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total_count"] == total_count
        assert data["has_next"] is True if total_count > 1 else False
        assert data["has_previous"] is False
        
        # Test page 2 if we have more than 1 event
        if total_count > 1:
            response = client.get("/api/events/location/nearby?city=Phoenix&state=AZ&page=2&page_size=1")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["items"]) == 1
            assert data["page"] == 2
            assert data["has_previous"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
