from fastapi import APIRouter, Depends, Body, Query
from app.services.user_service import (
    get_all_users,
    get_all_users_paginated
)

from app.auth.jwt_utils import get_current_user
from app.auth.roles import user_only, admin_only
from app.models.event import event as EventCreateRequest
from app.models import PaginatedUsersResponse, UserResponse
from app.models.pagination import PaginationParams, UserFilters
from app.utils.http_exceptions import HTTPExceptionHelper
from typing import Optional, List, Union

admin_router = APIRouter()

# Get all users (with optional pagination and filters)
@admin_router.get("/users", response_model=Union[PaginatedUsersResponse, dict])
async def fetch_all_users(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    profession: Optional[str] = Query(None, description="Filter by profession"),
    current_user: dict = Depends(admin_only)
):
    if page is not None:
        page_size = page_size or 10
        pagination = PaginationParams(page=page, page_size=page_size)
        filters = UserFilters(role=role, profession=profession)
        result = get_all_users_paginated(pagination, filters)
        
        # Convert to PaginatedUsersResponse format
        user_responses = []
        for user_dict in result.items:
            try:
                user_responses.append(UserResponse(**user_dict))
            except Exception as e:
                # Skip invalid users or log the error
                continue
                
        return PaginatedUsersResponse(
            items=user_responses,
            total_count=result.total_count,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_previous=result.has_previous
        )
    else:
        users = get_all_users()
        if users:
            return {"users": users}
        raise HTTPExceptionHelper.not_found("No users found")   