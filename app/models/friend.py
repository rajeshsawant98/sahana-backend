from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class FriendRequest(BaseModel):
    id: Optional[str] = None
    sender_id: str
    receiver_id: str
    status: Literal["pending", "accepted", "rejected"] = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FriendRequestCreate(BaseModel):
    receiver_id: str

class FriendRequestResponse(BaseModel):
    accept: bool

class FriendProfile(BaseModel):
    id: str
    name: str
    email: str
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    location: Optional[dict] = None
    interests: Optional[list] = None
    created_at: Optional[datetime] = None

class FriendRequestWithProfile(BaseModel):
    id: str
    sender: FriendProfile
    receiver: FriendProfile
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserSearchResult(BaseModel):
    id: str
    name: str
    email: str
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    location: Optional[dict] = None
    interests: Optional[list] = None
    friendship_status: Optional[Literal["friends", "pending_sent", "pending_received", "none"]] = "none"
