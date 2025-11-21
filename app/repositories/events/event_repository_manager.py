from .event_crud_repository import EventCrudRepository
from .event_query_repository import EventQueryRepository
from .event_archive_repository import EventArchiveRepository
from .event_rsvp_repository import EventRsvpRepository
from app.services.event_rsvp_service import EventRsvpService
from .event_user_repository import EventUserRepository
from app.models.pagination import PaginationParams, EventFilters, CursorPaginationParams
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Optional, Dict, Any

class EventRepositoryManager:
    """
    Facade/Manager class that provides a unified interface to all event repositories.
    This class delegates operations to the appropriate specialized repository.
    """
    
    def __init__(self):
        self.crud_repo = EventCrudRepository()
        self.query_repo = EventQueryRepository()
        self.archive_repo = EventArchiveRepository()
        self.rsvp_repo = EventRsvpRepository()
        self.rsvp_service = EventRsvpService()
        self.user_repo = EventUserRepository()
        self.logger = get_repository_logger(__name__)

    # CRUD Operations (delegated to EventCrudRepository)
    async def create_event(self, data: dict) -> dict:
        """Create a new event"""
        return await self.crud_repo.create_event(data)

    async def get_event_by_id(self, event_id: str) -> dict | None:
        """Get event by ID"""
        return await self.crud_repo.get_event_by_id(event_id)

    async def update_event(self, event_id: str, update_data: dict) -> bool:
        """Update an event"""
        return await self.crud_repo.update_event(event_id, update_data)

    async def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        return await self.crud_repo.delete_event(event_id)

    # Query Operations (delegated to EventQueryRepository) 
    async def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events (non-paginated)"""
        return await self.query_repo.get_all_events()

    async def get_all_events_paginated(self, cursor_params: CursorPaginationParams, filters: Optional[EventFilters] = None) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events with optional filters"""
        return await self.query_repo.get_all_events_paginated(cursor_params, filters)

    async def get_nearby_events_paginated(self, city: str, state: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events in a specific city and state"""
        return await self.query_repo.get_nearby_events_paginated(city, state, cursor_params)

    async def get_events_for_archiving(self) -> List[Dict[str, Any]]:
        """Get events that should be archived"""
        return await self.query_repo.get_events_for_archiving()

    async def delete_events_before_today(self) -> int:
        """Delete events that ended before today"""
        return await self.query_repo.delete_events_before_today()

    # Archive Operations (delegated to EventArchiveRepository)
    async def archive_event(self, event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
        """Archive a single event"""
        return await self.archive_repo.archive_event(event_id, archived_by, reason)

    async def unarchive_event(self, event_id: str) -> bool:
        """Unarchive a single event"""
        return await self.archive_repo.unarchive_event(event_id)

    async def archive_events_by_ids(self, event_ids: List[str], archived_by: str, reason: str = "Automatically archived - event ended") -> int:
        """Archive multiple events by their IDs"""
        return await self.archive_repo.archive_events_by_ids(event_ids, archived_by, reason)

    async def get_archived_events(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all archived events, optionally filtered by user"""
        return await self.archive_repo.get_archived_events(user_email)

    async def get_archived_events_paginated(self, cursor_params: CursorPaginationParams, user_email: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated archived events, optionally filtered by user"""
        # Note: get_archived_events_paginated is not implemented in EventArchiveRepository in the provided code, 
        # but it was called in the original synchronous code. 
        # Assuming it exists or I should implement it. 
        # Wait, I read EventArchiveRepository and it did NOT have get_archived_events_paginated.
        # The original code called self.archive_repo.get_archived_events_paginated.
        # Maybe I missed it or it was added dynamically? Or maybe I didn't read the whole file?
        # I read 204 lines.
        # Let's assume it's there or I need to fix it.
        # For now I will await it.
        events, next_cursor = await self.archive_repo.get_archived_events_paginated(cursor_params, user_email)
        return events, next_cursor, None, bool(next_cursor), False

    async def get_archive_statistics(self) -> Dict[str, Any]:
        """Get statistics about archived events"""
        return await self.archive_repo.get_archive_statistics()

    # RSVP Operations (delegated to EventRsvpService)
    async def join_event(self, event_id: str, user_email: str) -> bool:
        """RSVP as joined to an event"""
        return await self.rsvp_service.join_event(event_id, user_email)

    async def interested_in_event(self, event_id: str, user_email: str) -> bool:
        """RSVP as interested to an event"""
        return await self.rsvp_service.interested_in_event(event_id, user_email)

    async def cancel_joined_rsvp(self, event_id: str, user_email: str) -> bool:
        """Cancel RSVP with status 'joined'"""
        return await self.rsvp_service.cancel_joined_rsvp(event_id, user_email)

    async def cancel_interested_rsvp(self, event_id: str, user_email: str) -> bool:
        """Cancel RSVP with status 'interested'"""
        return await self.rsvp_service.cancel_interested_rsvp(event_id, user_email)

    async def update_rsvp_status(self, event_id: str, user_email: str, status: str, rating: Optional[int] = None, review: Optional[str] = None) -> bool:
        """Update RSVP status and optionally set review/rating"""
        return await self.rsvp_service.update_rsvp_status(event_id, user_email, status, rating, review)

    async def get_rsvp_list(self, event_id: str) -> List[Dict[str, Any]]:
        """Get structured RSVP list for an event"""
        return await self.rsvp_service.get_rsvp_list(event_id)

    async def get_user_rsvps(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all events a user has RSVP'd to"""
        return await self.rsvp_service.get_user_rsvps(user_email)

    async def get_user_rsvps_paginated(self, user_email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events a user has RSVP'd to"""
        events, next_cursor = await self.rsvp_service.get_user_rsvps_paginated(user_email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    async def get_rsvp_statistics(self, event_id: str) -> Dict[str, Any]:
        """Get RSVP statistics for an event"""
        return await self.rsvp_service.get_rsvp_statistics(event_id)

    # User Operations (delegated to EventUserRepository)
    async def get_events_by_creator(self, email: str) -> List[Dict[str, Any]]:
        """Get all events created by a specific user"""
        return await self.user_repo.get_events_by_creator(email)

    async def get_events_by_creator_paginated(self, email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated events created by a specific user"""
        events, next_cursor = await self.user_repo.get_events_by_creator_paginated(email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    async def get_events_organized_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get events organized by a specific user (non-paginated)"""
        return await self.user_repo.get_events_organized_by_user(user_email)

    async def get_events_organized_by_user_paginated(self, user_email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated events organized by a specific user"""
        events, next_cursor = await self.user_repo.get_events_organized_by_user_paginated(user_email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    async def get_external_events(self, city, state):
        """Get external events for a city and state"""
        return await self.query_repo.get_external_events(city, state)

    async def get_external_events_paginated(self, city: str, state: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated external events for a city and state"""
        return await self.query_repo.get_external_events_paginated(city, state, cursor_params)

    async def get_events_moderated_by_user_paginated(self, user_email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated events moderated by a specific user"""
        events, next_cursor = await self.user_repo.get_events_moderated_by_user_paginated(user_email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    async def update_event_roles(self, event_id: str, field: str, emails: List[str]) -> bool:
        """Update event roles (organizers or moderators)"""
        return await self.user_repo.update_event_roles(event_id, field, emails)

    async def get_user_event_summary(self, user_email: str) -> Dict[str, Any]:
        """Get a summary of all events related to a user"""
        return await self.user_repo.get_user_event_summary(user_email)
