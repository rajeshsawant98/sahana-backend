from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic, Optional, Dict, Any
import base64
import json

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page (max 100)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(cls, items: List[T], total_count: int, page: int, page_size: int):
        """Create a paginated response"""
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

class EventPaginatedResponse(PaginatedResponse[dict]):
    """Specific paginated response for events"""
    pass

class UserPaginatedResponse(PaginatedResponse[dict]):
    """Specific paginated response for users"""
    pass

# Optional filter models for more advanced pagination
class EventFilters(BaseModel):
    """Optional filters for event queries"""
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    is_online: Optional[bool] = None
    creator_email: Optional[str] = None
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None    # ISO format

class UserFilters(BaseModel):
    """Optional filters for user queries"""
    role: Optional[str] = None
    profession: Optional[str] = None

# Cursor-based pagination models
class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters"""
    cursor: Optional[str] = Field(default=None, description="Base64 encoded cursor for pagination position")
    page_size: int = Field(default=12, ge=1, le=100, description="Number of items per page (max 100)")
    direction: str = Field(default="next", pattern="^(next|prev)$", description="Pagination direction")

class CursorInfo(BaseModel):
    """Cursor position information"""
    start_time: Optional[str] = None  # ISO datetime string, can be None
    event_id: str    # Document ID for tie-breaking
    
    def encode(self) -> str:
        """Encode cursor info to base64 string"""
        cursor_dict = {"startTime": self.start_time, "eventId": self.event_id}
        return base64.b64encode(json.dumps(cursor_dict).encode()).decode()
    
    @classmethod
    def decode(cls, cursor: str) -> Optional["CursorInfo"]:
        """Decode base64 cursor string to CursorInfo"""
        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            data = json.loads(decoded)
            return cls(start_time=data["startTime"], event_id=data["eventId"])
        except Exception:
            return None

class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response"""
    items: List[T]
    pagination: Dict[str, Any]
    
    @classmethod
    def create(cls, items: List[T], next_cursor: Optional[str], prev_cursor: Optional[str], 
               has_next: bool, has_previous: bool, page_size: int):
        pagination_info = {
            "next_cursor": next_cursor,
            "prev_cursor": prev_cursor,
            "has_next": has_next,
            "has_previous": has_previous,
            "page_size": page_size
        }
            
        return cls(items=items, pagination=pagination_info)

class EventCursorPaginatedResponse(CursorPaginatedResponse[dict]):
    """Specific cursor-based paginated response for events"""
    pass
