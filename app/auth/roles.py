from fastapi import Depends, HTTPException, status
from app.auth.jwt_utils import get_current_user

ROLE_HIERARCHY = {
    "anonymous": 0,
    "user": 1,
    "admin": 2,
    "super_admin": 3
}

def require_min_role(min_role: str):
    def dependency(current_user: dict = Depends(get_current_user)):
        role = current_user.get("role", "anonymous")
        if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{min_role.replace('_', ' ').title()} access required"
            )
        return current_user
    return dependency

# 🎯 Shortcuts
user_only = require_min_role("user")
admin_only = require_min_role("admin")
super_admin_only = require_min_role("super_admin")