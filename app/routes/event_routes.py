from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.event_service import create_event, get_all_events, get_event_by_id, update_event

event_router = APIRouter()

# Event request model
class EventCreateRequest(BaseModel):
    eventName: str
    location: str
    startTime: str  # Should be in ISO format (e.g., "2025-02-01T15:30:00Z")
    duration: int  # Duration in minutes
    categories: List[str]
    isOnline: bool
    joinLink: Optional[str] = None
    imageURL: Optional[str] = None
    createdBy: str  # User ID or email of the event creator
    createdByEmail: str
    createdAt: Optional[str] = None

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