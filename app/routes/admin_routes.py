from fastapi import APIRouter, HTTPException, Depends, Body, Query
from app.services.user_service import (
    get_all_users,

)


from app.auth.jwt_utils import get_current_user
from app.auth.roles import user_only, admin_only
from app.auth.event_roles import require_event_creator, require_event_organizer, require_event_moderator
from app.models.event import event as EventCreateRequest

admin_router = APIRouter()

# Get all users (admin only)
@admin_router.get("/users")
async def fetch_all_users(current_user: dict = Depends(admin_only)):
    users = get_all_users()
    if users:
        return {"users": users}
    raise HTTPException(status_code=404, detail="No users found")   