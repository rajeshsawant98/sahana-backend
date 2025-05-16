from fastapi import Depends, HTTPException, status
from app.auth.jwt_utils import get_current_user

def require_role(role: str):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{role.title()} access required"
            )
        return current_user
    return dependency

# Common shortcut
admin_only = require_role("admin")