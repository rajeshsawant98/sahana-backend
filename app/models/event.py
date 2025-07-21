from pydantic import BaseModel , Field
from typing import List, Optional
from datetime import datetime


# RSVP object for event participants
class EventRsvp(BaseModel):
    email: str
    status: str  # "interested", "joined", "attended", "no_show"
    rating: Optional[int] = None  # Only if status == "attended"
    review: Optional[str] = None

class event(BaseModel):
    eventName: str
    location: dict
    startTime: str  # Should be in ISO format (e.g., "2025-02-01T15:30:00Z")
    duration: int = Field(..., gt=0)
    categories: List[str]
    isOnline: Optional[bool] = False
    joinLink: Optional[str] = None
    imageUrl: Optional[str] = None
    createdBy: str  # User ID or email of the event creator
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
