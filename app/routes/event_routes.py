from fastapi import APIRouter, HTTPException , Depends
from pydantic import BaseModel , Field
from typing import List, Optional
from app.services.event_service import create_event, get_all_events, get_event_by_id, update_event , rsvp_to_event
from app.auth.jwt_utils import get_current_user
from app.models.event import event as EventCreateRequest

event_router = APIRouter()

# Create event route
@event_router.post("/new")
async def create_new_event(event: EventCreateRequest):
    event_data = event.model_dump()
    result = create_event(event_data)

    if result:
        return {"message": "Event created successfully", "eventId": result["eventId"]}
    raise HTTPException(status_code=500, detail="Failed to create event")

# Get all events
@event_router.get("")
async def fetch_all_events():
    events = get_all_events()
    return {"events": events}

# Get event by ID
@event_router.get("/{event_id}")
async def fetch_event_by_id(event_id: str):
    event = get_event_by_id(event_id)
    if event:
        return event
    raise HTTPException(status_code=404, detail="Event not found")

# Update event
@event_router.put("/{event_id}")
async def modify_event(event_id: str, update_data: dict):
    success = update_event(event_id, update_data)
    if success:
        return {"message": "Event updated successfully"}
    raise HTTPException(status_code=404, detail="Failed to update event")

# Delete event


#RSVP to event
@event_router.post("/{event_id}/rsvp")
async def event_rsvp(event_id: str, current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    success = rsvp_to_event(event_id, email)
    if success:
        return {"message": "RSVP successful"}
    raise HTTPException(status_code=500, detail="Failed to RSVP")