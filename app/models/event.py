from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EventCreate(BaseModel):
    event_name: str
    location: str
    start_time: datetime
    duration: int  # Duration in minutes
    categories: List[str]
    is_online: bool
    link_to_join: Optional[str] = None  # Optional for now, will be used for Zoom link in future
    picture: Optional[str] = None  # URL or path to picture if available
    event_creator_name: str
    event_creator_email: str
