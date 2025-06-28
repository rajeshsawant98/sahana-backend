"""
Utility functions for handling pagination consistently across routes
"""
from fastapi import Query, HTTPException
from typing import Optional, Tuple
from app.models.pagination import PaginationParams

def pagination_params(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page")
) -> Optional[PaginationParams]:
    """
    Dependency for extracting pagination parameters from query params
    
    Returns:
        PaginationParams if page is provided, None for legacy mode
    """
    if page is not None:
        page_size = page_size or 10  # Default page size
        return PaginationParams(page=page, page_size=page_size)
    return None

def validate_pagination_params(page: Optional[int], page_size: Optional[int]) -> Tuple[bool, Optional[PaginationParams]]:
    """
    Validate and create pagination parameters
    
    Returns:
        (is_paginated, pagination_params)
    """
    if page is not None:
        if page < 1:
            raise HTTPException(status_code=400, detail="Page number must be >= 1")
        
        if page_size is not None and (page_size < 1 or page_size > 100):
            raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
        
        page_size = page_size or 10
        return True, PaginationParams(page=page, page_size=page_size)
    
    return False, None

def create_legacy_response(items: list, response_key: str = "events") -> dict:
    """
    Create legacy (non-paginated) response format
    
    Args:
        items: List of items to return
        response_key: Key name for the items in response
    """
    return {response_key: items, "count": len(items)}

def handle_paginated_response(
    paginated_func,
    legacy_func, 
    pagination_params: Optional[PaginationParams],
    response_key: str = "events",
    not_found_message: str = "No items found"
):
    """
    Generic handler for paginated vs legacy responses
    
    Args:
        paginated_func: Function to call for paginated response
        legacy_func: Function to call for legacy response  
        pagination_params: Pagination parameters (None for legacy)
        response_key: Key for items in legacy response
        not_found_message: Message when no items found in legacy mode
    """
    if pagination_params:
        # Paginated response
        return paginated_func(pagination_params)
    else:
        # Legacy response
        items = legacy_func()
        if not items:
            raise HTTPException(status_code=404, detail=not_found_message)
        return create_legacy_response(items, response_key)
