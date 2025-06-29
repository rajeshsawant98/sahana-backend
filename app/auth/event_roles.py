from fastapi import Depends, HTTPException, status
from app.auth.jwt_utils import get_current_user
from app.services.event_service import get_event_by_id

# ✅ Only creator or super_admin can pass
def require_event_creator(event_id: str, current_user: dict = Depends(get_current_user)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user.get("role") == "super_admin":
        return current_user
    if current_user["email"] != event.get("createdByEmail"):
        raise HTTPException(status_code=403, detail="Creator access required")
    return current_user

# ✅ Only organizer or super_admin can pass
def require_event_organizer(event_id: str, current_user: dict = Depends(get_current_user)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user.get("role") == "super_admin":
        return current_user
    if current_user["email"] not in event.get("organizers", []):
        raise HTTPException(status_code=403, detail="Organizer access required")
    return current_user

# ✅ Moderator, organizer, or super_admin can pass
def require_event_moderator(event_id: str, current_user: dict = Depends(get_current_user)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user.get("role") == "super_admin":
        return current_user
    email = current_user["email"]
    if email not in event.get("moderators", []) and email not in event.get("organizers", []):
        raise HTTPException(status_code=403, detail="Moderator or Organizer access required")
    return current_user

# ✅ Return the event if current user is the creator or super_admin
def get_event_if_creator(event_id: str, current_user: dict = Depends(get_current_user)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if current_user.get("role") == "super_admin":
        return event
    if current_user["email"] != event.get("createdByEmail"):
        raise HTTPException(status_code=403, detail="Only creator can access this")
    return event