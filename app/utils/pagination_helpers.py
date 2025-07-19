"""
Pagination helper functions to reduce code duplication in routes
"""
from fastapi import Query
from app.models.pagination import CursorPaginationParams
from typing import Optional


def get_cursor_pagination_params(
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    page_size: Optional[int] = Query(12, ge=1, le=100, description="Items per page"),
    direction: Optional[str] = Query("next", pattern="^(next|prev)$", description="Pagination direction")
) -> CursorPaginationParams:
    """
    Common pagination parameters dependency for cursor-based pagination.
    This reduces duplication across multiple route endpoints.
    """
    return CursorPaginationParams(
        cursor=cursor,
        page_size=page_size or 12,
        direction=direction or "next"
    )


def get_event_filter_params(
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_online: Optional[bool] = Query(None, description="Filter by online events"),
    creator_email: Optional[str] = Query(None, description="Filter by creator email"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)")
) -> dict:
    """
    Common event filter parameters dependency.
    Returns a dict that can be used to create EventFilters object.
    """
    return {
        "city": city,
        "state": state,
        "category": category,
        "is_online": is_online,
        "creator_email": creator_email,
        "start_date": start_date,
        "end_date": end_date
    }
