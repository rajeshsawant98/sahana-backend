from pydantic import BaseModel , Field
from typing import List, Optional
from datetime import datetime

class event(BaseModel):
    eventName: str
    location: dict
    startTime: str  # Should be in ISO format (e.g., "2025-02-01T15:30:00Z")
    duration: int = Field(..., gt=0)
    categories: List[str]
    isOnline: Optional[bool] = False
    joinLink: Optional[str] = None
    imageURL: Optional[str] = None
    createdBy: str  # User ID or email of the event creator
    createdByEmail: str
    createdAt: Optional[str] = None
    description: Optional[str] = None
