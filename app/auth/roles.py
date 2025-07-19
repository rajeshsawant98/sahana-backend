from fastapi import Depends, HTTPException, status
from app.auth.jwt_utils import get_current_user

# Role constants to avoid magic numbers
class RoleLevel:
    ANONYMOUS = 0
    USER = 1
    ADMIN = 2
    SUPER_ADMIN = 3

# Role names
class RoleName:
    ANONYMOUS = "anonymous"
    USER = "user" 
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

ROLE_HIERARCHY = {
    RoleName.ANONYMOUS: RoleLevel.ANONYMOUS,
    RoleName.USER: RoleLevel.USER,
    RoleName.ADMIN: RoleLevel.ADMIN,
    RoleName.SUPER_ADMIN: RoleLevel.SUPER_ADMIN
}

def require_min_role(min_role: str):
    def dependency(current_user: dict = Depends(get_current_user)):
        role = current_user.get("role", RoleName.ANONYMOUS)
        if ROLE_HIERARCHY.get(role, RoleLevel.ANONYMOUS) < ROLE_HIERARCHY[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{min_role.replace('_', ' ').title()} access required"
            )
        return current_user
    return dependency

# 🎯 Shortcuts
user_only = require_min_role(RoleName.USER)
admin_only = require_min_role(RoleName.ADMIN)
super_admin_only = require_min_role(RoleName.SUPER_ADMIN)