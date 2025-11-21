from app.repositories.users import UserRepository
from app.models.pagination import PaginationParams, UserPaginatedResponse, UserFilters
from app.utils.logger import get_service_logger
from typing import Optional

repo = UserRepository()
logger = get_service_logger(__name__)

async def get_user_by_email(email: str):
    return await repo.get_by_email(email)

async def get_user_by_id(uid: str):
    return await repo.get_by_id(uid)

async def store_user_with_password(email: str, password: str, name: str):
    return await repo.create_with_password(email, password, name)

async def verify_user_password(email: str, password: str):
    return await repo.verify_password(email, password)

async def update_user_data(user_data: dict, user_email: str):
    return await repo.update_profile_by_email(user_data, user_email)

async def store_or_update_user_data(user_data: dict):
    existing_user = await repo.get_by_email(user_data["email"])
    if existing_user:
        await repo.update_profile_by_email(user_data, user_data["email"])
    else:
        await repo.store_google_user(user_data)

# ✅ New function to validate email addresses (used in role assignment)
async def validate_user_emails(email_list: list[str]) -> dict:
    valid, invalid = [], []
    for email in email_list:
        if await repo.get_by_email(email):
            valid.append(email)
        else:
            invalid.append(email)
    return {
        "valid": valid,
        "invalid": invalid
    }

async def get_all_users():
    return await repo.get_all_users()

async def get_all_users_paginated(pagination: PaginationParams, filters: Optional[UserFilters] = None) -> UserPaginatedResponse:
    """Get paginated users with optional filters"""
    try:
        users, total_count = await repo.get_all_users_paginated(pagination, filters)
        return UserPaginatedResponse.create(users, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        logger.error(f"Error in get_all_users_paginated: {e}", exc_info=True)
        return UserPaginatedResponse.create([], 0, pagination.page, pagination.page_size)