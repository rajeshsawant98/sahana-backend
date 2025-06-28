from app.repositories.user_repository import UserRepository
from app.models.pagination import PaginationParams, UserPaginatedResponse, UserFilters
from typing import Optional

repo = UserRepository()

def get_user_by_email(email: str):
    return repo.get_by_email(email)

def get_user_by_id(uid: str):
    return repo.get_by_id(uid)

def store_user_with_password(email: str, password: str, name: str):
    return repo.create_with_password(email, password, name)

def verify_user_password(email: str, password: str):
    return repo.verify_password(email, password)

def update_user_data(user_data: dict, user_email: str):
    return repo.update_profile_by_email(user_data, user_email)

def store_or_update_user_data(user_data: dict):
    existing_user = repo.get_by_email(user_data["email"])
    if existing_user:
        repo.update_profile_by_email(user_data, user_data["email"])
    else:
        repo.store_google_user(user_data)

# ✅ New function to validate email addresses (used in role assignment)
def validate_user_emails(email_list: list[str]) -> dict:
    valid, invalid = [], []
    for email in email_list:
        if repo.get_by_email(email):
            valid.append(email)
        else:
            invalid.append(email)
    return {
        "valid": valid,
        "invalid": invalid
    }

def get_all_users():
    return repo.get_all_users()

def get_all_users_paginated(pagination: PaginationParams, filters: Optional[UserFilters] = None) -> UserPaginatedResponse:
    """Get paginated users with optional filters"""
    try:
        users, total_count = repo.get_all_users_paginated(pagination, filters)
        return UserPaginatedResponse.create(users, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_all_users_paginated: {e}")
        return UserPaginatedResponse.create([], 0, pagination.page, pagination.page_size)