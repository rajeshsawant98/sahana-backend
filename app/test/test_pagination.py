"""
Test file for pagination functionality
"""
import pytest
from app.models.pagination import PaginationParams, EventFilters, UserFilters, PaginatedResponse


def test_pagination_params_creation():
    """Test PaginationParams model creation and validation"""
    # Test default values
    pagination = PaginationParams()
    assert pagination.page == 1
    assert pagination.page_size == 10
    assert pagination.offset == 0
    
    # Test custom values
    pagination = PaginationParams(page=3, page_size=20)
    assert pagination.page == 3
    assert pagination.page_size == 20
    assert pagination.offset == 40  # (3-1) * 20
    
    # Test validation
    with pytest.raises(ValueError):
        PaginationParams(page=0)  # page must be >= 1
    
    with pytest.raises(ValueError):
        PaginationParams(page_size=0)  # page_size must be >= 1
    
    with pytest.raises(ValueError):
        PaginationParams(page_size=101)  # page_size must be <= 100


def test_event_filters_creation():
    """Test EventFilters model creation"""
    filters = EventFilters()
    assert filters.city is None
    assert filters.state is None
    assert filters.category is None
    assert filters.is_online is None
    
    filters = EventFilters(
        city="Austin",
        state="Texas", 
        category="Tech",
        is_online=True
    )
    assert filters.city == "Austin"
    assert filters.state == "Texas"
    assert filters.category == "Tech"
    assert filters.is_online is True


def test_user_filters_creation():
    """Test UserFilters model creation"""
    filters = UserFilters()
    assert filters.role is None
    assert filters.profession is None
    
    filters = UserFilters(role="admin", profession="Engineer")
    assert filters.role == "admin"
    assert filters.profession == "Engineer"


def test_paginated_response_creation():
    """Test PaginatedResponse model creation"""
    items = [{"id": 1}, {"id": 2}, {"id": 3}]
    total_count = 25
    page = 2
    page_size = 10
    
    response = PaginatedResponse.create(items, total_count, page, page_size)
    
    assert response.items == items
    assert response.total_count == 25
    assert response.page == 2
    assert response.page_size == 10
    assert response.total_pages == 3  # ceil(25/10)
    assert response.has_next is True
    assert response.has_previous is True
    
    # Test edge cases
    # First page
    response = PaginatedResponse.create(items, total_count, 1, page_size)
    assert response.has_previous is False
    assert response.has_next is True
    
    # Last page
    response = PaginatedResponse.create(items, total_count, 3, page_size)
    assert response.has_previous is True
    assert response.has_next is False
    
    # Single page
    response = PaginatedResponse.create(items, 5, 1, 10)
    assert response.has_previous is False
    assert response.has_next is False
    assert response.total_pages == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
