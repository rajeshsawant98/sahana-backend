from fastapi import APIRouter, HTTPException, Depends, Body, Query
from app.services.event_service import (
    create_event,
    get_all_events,
    get_all_events_paginated,
    get_event_by_id,
    get_events_moderated_by_user,
    get_events_moderated_by_user_paginated,
    get_events_organized_by_user,
    get_events_organized_by_user_paginated,
    update_event,
    delete_event,
    get_my_events,
    get_my_events_paginated,
    rsvp_to_event,
    cancel_user_rsvp,
    get_user_rsvps,
    get_user_rsvps_paginated,
    get_nearby_events,
    get_nearby_events_paginated,
    get_external_events,
    get_external_events_paginated,
    set_organizers,
    set_moderators,
    archive_event,
    unarchive_event,
    is_event_past,
    get_archived_events,
    get_archived_events_paginated,
    archive_past_events,
    get_rsvp_list
)

from app.services.event_ingestion_service import (
    fetch_ticketmaster_events,
    ingest_bulk_events,
    ingest_events_for_all_cities
)

from app.auth.jwt_utils import get_current_user
from app.auth.roles import user_only, admin_only
from app.auth.event_roles import require_event_creator, require_event_organizer, require_event_moderator
from app.models.event import event as EventCreateRequest
from app.models.pagination import PaginationParams, EventFilters
from typing import Optional

event_router = APIRouter()

# Create a new event
@event_router.post("/new")
async def create_new_event(event: EventCreateRequest , current_user: dict = Depends(user_only)):
    event_data = event.model_dump()
    result = create_event(event_data)
    if result:
        return {"message": "Event created successfully", "eventId": result["eventId"]}
    raise HTTPException(status_code=500, detail="Failed to create event")

# Get all events (with optional pagination and filters)
@event_router.get("")
async def fetch_all_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_online: Optional[bool] = Query(None, description="Filter by online events"),
    creator_email: Optional[str] = Query(None, description="Filter by creator email"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)")
):
    # If page is provided, use pagination
    if page is not None:
        page_size = page_size or 10  # Default to 10 if not specified
        pagination = PaginationParams(page=page, page_size=page_size)
        filters = EventFilters(
            city=city,
            state=state,
            category=category,
            is_online=is_online,
            creator_email=creator_email,
            start_date=start_date,
            end_date=end_date
        )
        return get_all_events_paginated(pagination, filters)
    else:
        # Legacy behavior - return all events
        events = get_all_events()
        return {"events": events}

# Get archived events (creator only) with optional pagination
@event_router.get("/me/archived")
async def get_my_archived_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(user_only)
):
    user_email = current_user["email"]
    
    if page is not None:
        page_size = page_size or 10
        pagination = PaginationParams(page=page, page_size=page_size)
        return get_archived_events_paginated(pagination, user_email)
    else:
        archived_events = get_archived_events(user_email)
        return {"archived_events": archived_events, "count": len(archived_events)}

# Get all archived events (admin only) with optional pagination
@event_router.get("/archived")
async def get_all_archived_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(admin_only)
):
    """Get all archived events across the system (admin only)"""
    try:
        if page is not None:
            page_size = page_size or 10
            pagination = PaginationParams(page=page, page_size=page_size)
            return get_archived_events_paginated(pagination)  # No user filter = get all
        else:
            archived_events = get_archived_events()  # No user filter = get all
            return {
                "archived_events": archived_events, 
                "count": len(archived_events),
                "message": f"Retrieved {len(archived_events)} archived events"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve archived events: {str(e)}")

# Get event by ID
@event_router.get("/{event_id}")
async def fetch_event_by_id(event_id: str):
    event = get_event_by_id(event_id)
    if event:
        return event
    raise HTTPException(status_code=404, detail="Event not found")

# Update event (creator only)
@event_router.put("/{event_id}")
async def modify_event(event_id: str, update_data: dict, current_user: dict = Depends(require_event_creator)):
    success = update_event(event_id, update_data)
    if success:
        return {"message": "Event updated successfully"}
    raise HTTPException(status_code=500, detail="Failed to update event")

# Delete event (creator only)
@event_router.delete("/{event_id}")
async def remove_event(event_id: str, current_user: dict = Depends(require_event_creator)):
    success = delete_event(event_id)
    if success:
        return {"message": "Event deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete event")

# Archive event (creator only)
@event_router.patch("/{event_id}/archive")
async def archive_event_endpoint(
    event_id: str, 
    archive_data: dict = Body({"reason": "Event archived"}),
    current_user: dict = Depends(require_event_creator)
):
    # Get the event to check if it exists and if it's in the past
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if event is in the past (optional validation)
    if not is_event_past(event):
        # You can choose to allow or disallow archiving future events
        # For now, we'll allow it but add a warning in the response
        pass
    
    reason = archive_data.get("reason", "Event archived")
    archived_by = current_user["email"]
    
    success = archive_event(event_id, archived_by, reason)
    if success:
        message = "Event archived successfully"
        if not is_event_past(event):
            message += " (Note: This event has not ended yet)"
        return {"message": message, "archived_by": archived_by, "reason": reason}
    raise HTTPException(status_code=500, detail="Failed to archive event")

# Unarchive event (creator only)
@event_router.patch("/{event_id}/unarchive")
async def unarchive_event_endpoint(event_id: str, current_user: dict = Depends(require_event_creator)):
    success = unarchive_event(event_id)
    if success:
        return {"message": "Event restored successfully"}
    raise HTTPException(status_code=500, detail="Failed to restore event")

# Events created by user (with optional pagination)
@event_router.get("/me/created")
async def fetch_my_created_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(user_only)
):
    email = current_user["email"]
    
    if page is not None:
        page_size = page_size or 10
        pagination = PaginationParams(page=page, page_size=page_size)
        return get_my_events_paginated(email, pagination)
    else:
        events = get_my_events(email)
        if events:
            return {"message": "Events fetched successfully", "events": events}
        raise HTTPException(status_code=404, detail="No events found for the user")

# Events RSVP'd by user (with optional pagination)
@event_router.get("/me/rsvped")
async def fetch_user_rsvped_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(user_only)
):
    try:
        email = current_user["email"]
        
        if page is not None:
            page_size = page_size or 10
            pagination = PaginationParams(page=page, page_size=page_size)
            return get_user_rsvps_paginated(email, pagination)
        else:
            events = get_user_rsvps(email)
            if not events:
                raise HTTPException(status_code=404, detail="No RSVP'd events found")
            return {"message": "RSVP'd events fetched", "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Events organized by user (with optional pagination)
@event_router.get("/me/organized")
async def fetch_user_organized_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(user_only)
):
    try:
        email = current_user["email"]
        
        if page is not None:
            page_size = page_size or 10
            pagination = PaginationParams(page=page, page_size=page_size)
            return get_events_organized_by_user_paginated(email, pagination)
        else:
            events = get_events_organized_by_user(email)
            if not events:
                raise HTTPException(status_code=404, detail="No organized events found")
            return {"message": "Organized events fetched", "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Events moderated by user (with optional pagination)
@event_router.get("/me/moderated")
async def fetch_user_moderated_events(
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(user_only)
):
    try:
        email = current_user["email"]
        
        if page is not None:
            page_size = page_size or 10
            pagination = PaginationParams(page=page, page_size=page_size)
            return get_events_moderated_by_user_paginated(email, pagination)
        else:
            events = get_events_moderated_by_user(email)
            if not events:
                raise HTTPException(status_code=404, detail="No moderated events found")
            return {"message": "Moderated events fetched", "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Fetch + Ingest Ticketmaster events (per city/state)
@event_router.post("/fetch-ticketmaster-events")
def fetch_and_ingest_ticketmaster(payload: dict = Body(...), current_user: dict = Depends(admin_only)):
    city = payload.get("city")
    state = payload.get("state")

    if not city or not state:
        raise HTTPException(status_code=400, detail="City and state are required.")

    raw_events = fetch_ticketmaster_events(city, state)
    summary = ingest_bulk_events(raw_events)

    return {
        "message": f"{summary['saved']} new events ingested, {summary['skipped']} skipped.",
        "sample": raw_events[:3]
    }

# External events by location (with optional pagination)
@event_router.get("/location/external")
def list_external_events(
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State name"),
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(user_only)
):
    if page is not None:
        page_size = page_size or 10
        pagination = PaginationParams(page=page, page_size=page_size)
        return get_external_events_paginated(city, state, pagination)
    else:
        events = get_external_events(city, state)
        return {"events": events, "count": len(events)}

# Nearby community events by city/state (with optional pagination)
@event_router.get("/location/nearby")
def list_nearby_events(
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State name"),
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page")
):
    if page is not None:
        page_size = page_size or 10
        pagination = PaginationParams(page=page, page_size=page_size)
        return get_nearby_events_paginated(city, state, pagination)
    else:
        events = get_nearby_events(city, state)
        return {"events": events, "count": len(events)}

@event_router.patch("/{event_id}/organizers")
async def update_event_organizers(
    event_id: str,
    payload: dict = Body(...),
    current_user: dict = Depends(require_event_creator)
):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_organizers = payload.get("organizerEmails", [])
    creator_email = event.get("createdByEmail")

    if creator_email is None:
        raise HTTPException(status_code=500, detail="Event creator email is missing.")

    result = set_organizers(event_id, new_organizers, creator_email)

    if result["success"]:
        return {
            "message": "Organizers updated",
            "organizerIds": result["organizerIds"],
            "skipped": result["skipped"]
        }
    raise HTTPException(status_code=500, detail="Failed to update organizers")

@event_router.patch("/{event_id}/moderators")
async def update_event_moderators(
    event_id: str,
    payload: dict = Body(...),
    current_user: dict = Depends(require_event_organizer)
):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_moderators = payload.get("moderatorEmails", [])
    result = set_moderators(event_id, new_moderators)

    if result["success"]:
        return {
            "message": "Moderators updated",
            "moderatorIds": result["moderatorIds"],
            "skipped": result["skipped"]
        }

    raise HTTPException(status_code=500, detail="Failed to update moderators")

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
        raise HTTPException(status_code=500, detail=f"Failed to archive past events: {str(e)}")

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
            # Get updated event info for response
            event = get_event_by_id(event_id)
            rsvp_list = event.get("rsvpList", []) if event else []
            
            return {
                "message": "Successfully RSVP'd to event",
                "rsvp_status": "going",
                "event": {
                    "id": event_id,
                    "title": event.get("eventName", "") if event else "",
                    "current_attendees": len(rsvp_list)
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to RSVP to event")
            
    except ValueError as e:
        # Handle business logic validation errors
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already RSVP'd" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to RSVP to event: {str(e)}")

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
            # Get updated event info for response
            event = get_event_by_id(event_id)
            rsvp_list = event.get("rsvpList", []) if event else []
            
            return {
                "message": "RSVP cancelled successfully",
                "rsvp_status": None,
                "event": {
                    "id": event_id,
                    "title": event.get("eventName", "") if event else "",
                    "current_attendees": len(rsvp_list)
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel RSVP")
            
    except ValueError as e:
        # Handle business logic validation errors
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel RSVP: {str(e)}")

@event_router.get("/{event_id}/rsvps")
async def get_event_rsvps(
    event_id: str,
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page")
):
    """Get RSVP list for an event"""
    try:
        rsvp_list = get_rsvp_list(event_id)
        
        if page is not None:
            # Paginated response
            page_size = page_size or 10
            total_count = len(rsvp_list)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_rsvps = rsvp_list[start_idx:end_idx]
            
            return {
                "items": [{"user_email": email} for email in paginated_rsvps],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": end_idx < total_count,
                    "has_prev": page > 1
                }
            }
        else:
            # Non-paginated response
            return {
                "rsvp_list": rsvp_list,
                "total_count": len(rsvp_list)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RSVP list: {str(e)}")