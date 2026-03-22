from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.user import Location


# RSVP object for event participants
class EventRsvp(BaseModel):
    email: str
    status: str  # "interested", "joined", "attended", "no_show"
    rating: Optional[int] = None  # Only if status == "attended"
    review: Optional[str] = None


class Event(BaseModel):
    eventName: str
    location: Optional[Location] = None
    startTime: str  # ISO format (e.g., "2025-02-01T15:30:00Z")
    duration: int = Field(..., gt=0)
    categories: List[str]
    isOnline: Optional[bool] = False
    joinLink: Optional[str] = None
    imageUrl: Optional[str] = None
    createdBy: str  # email of the event creator
    createdByEmail: str
    createdAt: Optional[str] = None
    description: Optional[str] = None
    # Archive/soft delete fields
    isArchived: Optional[bool] = False
    archivedAt: Optional[str] = None
    archivedBy: Optional[str] = None
    archiveReason: Optional[str] = None
    # RSVP list as array of objects
    rsvpList: Optional[List[EventRsvp]] = None


# Keep alias for any code still referencing lowercase name
event = Event
