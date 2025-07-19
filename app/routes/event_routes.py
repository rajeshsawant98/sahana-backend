from fastapi import APIRouter, Depends, Body, Query
from app.services.event_service import (
    create_event,
    get_all_events_paginated,
    get_event_by_id,
    get_events_moderated_by_user_paginated,
    get_events_organized_by_user_paginated,
    update_event,
    delete_event,
    get_my_events_paginated,
    rsvp_to_event,
    cancel_user_rsvp,
    get_user_rsvps_paginated,
    get_nearby_events_paginated,
    set_organizers,
    set_moderators,
    unarchive_event,
    get_archived_events_paginated,
    archive_past_events,
    get_rsvp_list,
    get_rsvp_response_data,
    get_paginated_rsvp_list,
    archive_event_with_validation
)

from app.services.event_ingestion_service import (
    fetch_ticketmaster_events,
    ingest_bulk_events,
    ingest_events_for_all_cities
)

from app.auth.jwt_utils import get_current_user
from app.auth.roles import user_only, admin_only
from app.auth.event_roles import require_event_creator, require_event_organizer
from app.models.event import event as EventCreateRequest
from app.models.pagination import EventFilters, CursorPaginationParams
from app.utils.pagination_helpers import get_cursor_pagination_params, get_event_filter_params
from app.utils.http_exceptions import event_not_found, operation_failed, HTTPExceptionHelper
from typing import Optional

event_router = APIRouter()

# Create a new event
@event_router.post("/new")
async def create_new_event(event: EventCreateRequest , current_user: dict = Depends(user_only)):
    event_data = event.model_dump()
    result = create_event(event_data)
    if result:
        return {"message": "Event created successfully", "eventId": result["eventId"]}
    raise operation_failed("create event")

# Get all events (cursor pagination by default)
@event_router.get("")
async def fetch_all_events(
    cursor_params: CursorPaginationParams = Depends(get_cursor_pagination_params),
    filter_params: dict = Depends(get_event_filter_params)
):
    filters = EventFilters(**filter_params)
    return get_all_events_paginated(cursor_params, filters)

# Get archived events (creator only) with cursor pagination
@event_router.get("/me/archived")
async def get_my_archived_events(
    cursor_params: CursorPaginationParams = Depends(get_cursor_pagination_params),
    current_user: dict = Depends(user_only)
):
    user_email = current_user["email"]
    return get_archived_events_paginated(cursor_params, user_email)

# Get all archived events (admin only) with cursor pagination
@event_router.get("/archived")
async def get_all_archived_events(
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    page_size: Optional[int] = Query(10, ge=1, le=100, description="Items per page"),
    direction: Optional[str] = Query("next", pattern="^(next|prev)$", description="Pagination direction"),
    current_user: dict = Depends(admin_only)
):
    """Get all archived events across the system (admin only)"""
    try:
        cursor_params = CursorPaginationParams(
            cursor=cursor,
            page_size=page_size or 10,
            direction=direction or "next"
        )
        return get_archived_events_paginated(cursor_params)  # No user filter = get all
    except Exception as e:
        raise HTTPExceptionHelper.server_error(f"Failed to retrieve archived events: {str(e)}")

# Get event by ID
@event_router.get("/{event_id}")
async def fetch_event_by_id(event_id: str):
    event = get_event_by_id(event_id)
    if event:
        return event
    raise event_not_found()

# Update event (creator only)
@event_router.put("/{event_id}")
async def update_existing_event(event_id: str, update_data: dict = Body(...), current_user: dict = Depends(require_event_creator)):
    success = update_event(event_id, update_data)
    if success:
        return {"message": "Event updated successfully"}
    raise operation_failed("update event")

# Delete event (creator only)
@event_router.delete("/{event_id}")
async def delete_existing_event(event_id: str, current_user: dict = Depends(require_event_creator)):
    success = delete_event(event_id)
    if success:
        return {"message": "Event deleted successfully"}
    raise operation_failed("delete event")

# Archive event (creator only)
@event_router.patch("/{event_id}/archive")
async def archive_event_endpoint(
    event_id: str, 
    archive_data: dict = Body({"reason": "Event archived"}),
    current_user: dict = Depends(require_event_creator)
):
    """Archive an event with validation"""
    reason = archive_data.get("reason", "Event archived")
    archived_by = current_user["email"]
    
    result = archive_event_with_validation(event_id, archived_by, reason)
    
    if result["success"]:
        return {
            "message": result["message"],
            "archived_by": result["archived_by"],
            "reason": result["reason"]
        }
    else:
        error_type = result.get("error_type", "server_error")
        if error_type == "not_found":
            raise HTTPExceptionHelper.not_found(result["error"])
        else:
            raise HTTPExceptionHelper.server_error(result["error"])

# Unarchive event (creator only)
@event_router.patch("/{event_id}/unarchive")
async def unarchive_event_endpoint(event_id: str, current_user: dict = Depends(require_event_creator)):
    success = unarchive_event(event_id)
    if success:
        return {"message": "Event restored successfully"}
    raise HTTPExceptionHelper.server_error("Failed to restore event")

# Events created by user (cursor pagination)
@event_router.get("/me/created")
async def fetch_my_created_events(
    cursor_params: CursorPaginationParams = Depends(get_cursor_pagination_params),
    current_user: dict = Depends(user_only)
):
    email = current_user["email"]
    return get_my_events_paginated(email, cursor_params)

# Events RSVP'd by user (cursor pagination)
@event_router.get("/me/rsvped")
async def fetch_user_rsvped_events(
    cursor_params: CursorPaginationParams = Depends(get_cursor_pagination_params),
    current_user: dict = Depends(user_only)
):
    try:
        email = current_user["email"]
        return get_user_rsvps_paginated(email, cursor_params)
    except Exception as e:
        raise HTTPExceptionHelper.server_error(str(e))

# Events organized by user (cursor pagination)

# Events organized by user (cursor pagination)
@event_router.get("/me/organized")
async def fetch_user_organized_events(
    cursor_params: CursorPaginationParams = Depends(get_cursor_pagination_params),
    current_user: dict = Depends(user_only)
):
    try:
        email = current_user["email"]
        return get_events_organized_by_user_paginated(email, cursor_params)
    except Exception as e:
        raise HTTPExceptionHelper.server_error(str(e))

# Events moderated by user (cursor pagination)
@event_router.get("/me/moderated")
async def fetch_user_moderated_events(
    cursor_params: CursorPaginationParams = Depends(get_cursor_pagination_params),
    current_user: dict = Depends(user_only)
):
    try:
        email = current_user["email"]
        return get_events_moderated_by_user_paginated(email, cursor_params)
    except Exception as e:
        raise HTTPExceptionHelper.server_error(str(e))
    
# Fetch + Ingest Ticketmaster events (per city/state)
@event_router.post("/fetch-ticketmaster-events")
def fetch_and_ingest_ticketmaster(payload: dict = Body(...), current_user: dict = Depends(admin_only)):
    city = payload.get("city")
    state = payload.get("state")

    if not city or not state:
        raise HTTPExceptionHelper.bad_request("City and state are required.")

    raw_events = fetch_ticketmaster_events(city, state)
    summary = ingest_bulk_events(raw_events)

    return {
        "message": f"{summary['saved']} new events ingested, {summary['skipped']} skipped.",
        "sample": raw_events[:3]
    }

# Nearby community events by city/state (cursor pagination)
@event_router.get("/location/nearby")
def list_nearby_events(
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State name"),
    # Cursor pagination parameters
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    page_size: Optional[int] = Query(12, ge=1, le=100, description="Items per page"),
    direction: Optional[str] = Query("next", pattern="^(next|prev)$", description="Pagination direction")
):
    # Use cursor-based pagination
    cursor_params = CursorPaginationParams(
        cursor=cursor,
        page_size=page_size or 12,
        direction=direction or "next"
    )
    return get_nearby_events_paginated(city, state, cursor_params)

@event_router.patch("/{event_id}/organizers")
async def update_event_organizers(
    event_id: str,
    payload: dict = Body(...),
    current_user: dict = Depends(require_event_creator)
):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPExceptionHelper.not_found("Event not found")

    new_organizers = payload.get("organizerEmails", [])
    creator_email = event.get("createdByEmail")

    if creator_email is None:
        raise HTTPExceptionHelper.server_error("Event creator email is missing.")

    result = set_organizers(event_id, new_organizers, creator_email)

    if result["success"]:
        return {
            "message": "Organizers updated",
            "organizers": result["organizers"],  # Changed from "organizerIds" to "organizers"
            "skipped": result["skipped"]
        }
    raise HTTPExceptionHelper.server_error("Failed to update organizers")

@event_router.patch("/{event_id}/moderators")
async def update_event_moderators(
    event_id: str,
    payload: dict = Body(...),
    current_user: dict = Depends(require_event_organizer)
):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPExceptionHelper.not_found("Event not found")

    new_moderators = payload.get("moderatorEmails", [])
    result = set_moderators(event_id, new_moderators)

    if result["success"]:
        return {
            "message": "Moderators updated",
            "moderators": result["moderators"],  # Changed from "moderatorIds" to "moderators"
            "skipped": result["skipped"]
        }

    raise HTTPExceptionHelper.server_error("Failed to update moderators")

@event_router.post("/ingest/all")
async def ingest_for_all_user_locations(current_user: dict = Depends(admin_only)):
    result = await ingest_events_for_all_cities()
    return result

# Bulk archive past events (admin only)
@event_router.post("/archive/past-events")
async def bulk_archive_past_events(current_user: dict = Depends(admin_only)):
    """Archive all events that have ended (admin only)"""
    try:
        archived_count = archive_past_events(current_user.get("email", "admin"))
        return {
            "message": f"Successfully archived {archived_count} past events",
            "archived_count": archived_count
        }
    except Exception as e:
        raise HTTPExceptionHelper.server_error(f"Failed to archive past events: {str(e)}")

# ========== RSVP ENDPOINTS ==========

@event_router.post("/{event_id}/rsvp")
async def rsvp_to_event_endpoint(
    event_id: str,
    current_user: dict = Depends(user_only)
):
    """RSVP to an event"""
    try:
        email = current_user["email"]
        success = rsvp_to_event(event_id, email)
        
        if success:
            return get_rsvp_response_data(event_id, email, "created")
        else:
            raise HTTPExceptionHelper.server_error("Failed to RSVP to event")
            
    except ValueError as e:
        # Handle business logic validation errors
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPExceptionHelper.not_found(error_msg)
        elif "already RSVP'd" in error_msg:
            raise HTTPExceptionHelper.conflict(error_msg)
        else:
            raise HTTPExceptionHelper.bad_request(error_msg)
    except Exception as e:
        raise HTTPExceptionHelper.server_error(f"Failed to RSVP to event: {str(e)}")

@event_router.delete("/{event_id}/rsvp")
async def cancel_rsvp_endpoint(
    event_id: str,
    current_user: dict = Depends(user_only)
):
    """Cancel RSVP to an event"""
    try:
        email = current_user["email"]
        success = cancel_user_rsvp(event_id, email)
        
        if success:
            return get_rsvp_response_data(event_id, email, "cancelled")
        else:
            raise HTTPExceptionHelper.server_error("Failed to cancel RSVP")
            
    except ValueError as e:
        # Handle business logic validation errors
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPExceptionHelper.not_found(error_msg)
        else:
            raise HTTPExceptionHelper.bad_request(error_msg)
    except Exception as e:
        raise HTTPExceptionHelper.server_error(f"Failed to cancel RSVP: {str(e)}")

@event_router.get("/{event_id}/rsvps")
async def get_event_rsvps(
    event_id: str,
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page")
):
    """Get RSVP list for an event"""
    try:
        page_size = page_size or 10
        return get_paginated_rsvp_list(event_id, page, page_size)
            
    except Exception as e:
        raise HTTPExceptionHelper.server_error(f"Failed to get RSVP list: {str(e)}")

# Export the router for the application
router = event_router