from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from google.cloud import firestore  # Firestore library

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class Location(BaseModel):
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    formattedAddress: Optional[str] = None
    name: Optional[str] = None

class User(BaseModel):
    """Base User model matching Firestore schema"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str  # Hashed password stored in Firestore
    interests: Optional[List[str]] = Field(default=[])
    profession: Optional[str] = Field(default="", max_length=100)
    bio: Optional[str] = Field(default="", max_length=500)
    phoneNumber: Optional[str] = Field(default="", max_length=20)
    location: Optional[Location] = None
    birthdate: Optional[str] = Field(default="")  # Format: YYYY-MM-DD
    role: Optional[UserRole] = Field(default=UserRole.USER)
    profile_picture: Optional[str] = Field(default="")
    google_uid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('interests', pre=True, always=True)
    def validate_interests(cls, v):
        if v is None:
            return []
        
        # Basic validation - ensure it's a list of strings
        if not isinstance(v, list):
            raise ValueError("Interests must be a list")
        
        # Validate each interest is a non-empty string
        for interest in v:
            if not isinstance(interest, str) or not interest.strip():
                raise ValueError("Each interest must be a non-empty string")
        
        # Remove duplicates and trim whitespace
        cleaned_interests = list(set(interest.strip() for interest in v))
        
        return cleaned_interests

    @validator('birthdate')
    def validate_birthdate(cls, v):
        if v and v != "":
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Birthdate must be in YYYY-MM-DD format")
        return v

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """Model for creating new users"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phoneNumber: Optional[str] = Field(default="", max_length=20)
    bio: Optional[str] = Field(default="", max_length=500)
    birthdate: Optional[str] = Field(default="")
    profession: Optional[str] = Field(default="", max_length=100)
    profile_picture: Optional[str] = Field(default="")
    interests: Optional[List[str]] = Field(default=[])
    location: Optional[Location] = None
    role: Optional[UserRole] = Field(default=UserRole.USER)

    @validator('interests', pre=True, always=True)
    def validate_interests(cls, v):
        if v is None:
            return []
        
        # Basic validation - ensure it's a list of strings
        if not isinstance(v, list):
            raise ValueError("Interests must be a list")
        
        # Validate each interest is a non-empty string
        for interest in v:
            if not isinstance(interest, str) or not interest.strip():
                raise ValueError("Each interest must be a non-empty string")
        
        # Remove duplicates and trim whitespace
        cleaned_interests = list(set(interest.strip() for interest in v))
        
        return cleaned_interests

    @validator('birthdate')
    def validate_birthdate(cls, v):
        if v and v != "":
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Birthdate must be in YYYY-MM-DD format")
        return v

class UserUpdate(BaseModel):
    """Model for updating user profiles"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phoneNumber: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    birthdate: Optional[str] = None
    profession: Optional[str] = Field(None, max_length=100)
    profile_picture: Optional[str] = None
    interests: Optional[List[str]] = None
    location: Optional[Location] = None

    @validator('interests', pre=True, allow_reuse=True)
    def validate_interests(cls, v):
        if v is None:
            return v
        
        # Basic validation - ensure it's a list of strings
        if not isinstance(v, list):
            raise ValueError("Interests must be a list")
        
        # Validate each interest is a non-empty string
        for interest in v:
            if not isinstance(interest, str) or not interest.strip():
                raise ValueError("Each interest must be a non-empty string")
        
        # Remove duplicates and trim whitespace
        cleaned_interests = list(set(interest.strip() for interest in v))
        
        return cleaned_interests

    @validator('birthdate', allow_reuse=True)
    def validate_birthdate(cls, v):
        if v and v != "":
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Birthdate must be in YYYY-MM-DD format")
        return v

class UserResponse(BaseModel):
    """Model for API responses (excludes password)"""
    name: str
    email: EmailStr
    phoneNumber: Optional[str] = ""
    bio: Optional[str] = ""
    birthdate: Optional[str] = ""
    profession: Optional[str] = ""
    interests: Optional[List[str]] = []
    role: UserRole
    profile_picture: Optional[str] = ""
    location: Optional[Location] = None
    google_uid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    """Public user profile for search results and friend lists"""
    name: str
    email: EmailStr
    bio: Optional[str] = ""
    profession: Optional[str] = ""
    profile_picture: Optional[str] = ""
    interests: Optional[List[str]] = []
    location: Optional[Location] = None

class UserSearchResult(BaseModel):
    """User search result with friendship status"""
    name: str
    email: EmailStr
    bio: Optional[str] = ""
    profession: Optional[str] = ""
    profile_picture: Optional[str] = ""
    interests: Optional[List[str]] = []
    location: Optional[Location] = None
    friendship_status: Optional[str] = None  # "friends", "pending", "none"

class GoogleUserCreate(BaseModel):
    """Model for creating users via Google OAuth"""
    name: str
    email: EmailStr
    google_uid: str
    profile_picture: Optional[str] = ""

class UserLoginRequest(BaseModel):
    """Model for login requests"""
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    """Simple authentication response - only essential data"""
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    email: EmailStr

class UserLoginResponseLegacy(BaseModel):
    """Legacy model with full user data - for backward compatibility if needed"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class PaginatedUsersResponse(BaseModel):
    """Model for paginated user responses"""
    items: List[UserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

class UserStatsResponse(BaseModel):
    """User statistics for dashboard"""
    events_created: int = 0
    events_attended: int = 0
    friends_count: int = 0
    pending_requests: int = 0