from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic, Optional

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
