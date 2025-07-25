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
    def create_event(self, data: dict) -> dict:
        """Create a new event"""
        return self.crud_repo.create_event(data)

    def get_event_by_id(self, event_id: str) -> dict | None:
        """Get event by ID"""
        return self.crud_repo.get_event_by_id(event_id)

    def update_event(self, event_id: str, update_data: dict) -> bool:
        """Update an event"""
        return self.crud_repo.update_event(event_id, update_data)

    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        return self.crud_repo.delete_event(event_id)

    # Query Operations (delegated to EventQueryRepository) 
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events (non-paginated)"""
        return self.query_repo.get_all_events()

    def get_all_events_paginated(self, cursor_params: CursorPaginationParams, filters: Optional[EventFilters] = None) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events with optional filters"""
        return self.query_repo.get_all_events_paginated(cursor_params, filters)

    def get_nearby_events_paginated(self, city: str, state: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events in a specific city and state"""
        return self.query_repo.get_nearby_events_paginated(city, state, cursor_params)

    def get_events_for_archiving(self) -> List[Dict[str, Any]]:
        """Get events that should be archived"""
        return self.query_repo.get_events_for_archiving()

    def delete_events_before_today(self) -> int:
        """Delete events that ended before today"""
        return self.query_repo.delete_events_before_today()

    # Archive Operations (delegated to EventArchiveRepository)
    def archive_event(self, event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
        """Archive a single event"""
        return self.archive_repo.archive_event(event_id, archived_by, reason)

    def unarchive_event(self, event_id: str) -> bool:
        """Unarchive a single event"""
        return self.archive_repo.unarchive_event(event_id)

    def archive_events_by_ids(self, event_ids: List[str], archived_by: str, reason: str = "Automatically archived - event ended") -> int:
        """Archive multiple events by their IDs"""
        return self.archive_repo.archive_events_by_ids(event_ids, archived_by, reason)

    def get_archived_events(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all archived events, optionally filtered by user"""
        return self.archive_repo.get_archived_events(user_email)

    def get_archived_events_paginated(self, cursor_params: CursorPaginationParams, user_email: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated archived events, optionally filtered by user"""
        events, next_cursor = self.archive_repo.get_archived_events_paginated(cursor_params, user_email)
        return events, next_cursor, None, bool(next_cursor), False

    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get statistics about archived events"""
        return self.archive_repo.get_archive_statistics()

    # RSVP Operations (delegated to EventRsvpService)
    def join_event(self, event_id: str, user_email: str) -> bool:
        """RSVP as joined to an event"""
        return self.rsvp_service.join_event(event_id, user_email)

    def interested_in_event(self, event_id: str, user_email: str) -> bool:
        """RSVP as interested to an event"""
        return self.rsvp_service.interested_in_event(event_id, user_email)

    def cancel_joined_rsvp(self, event_id: str, user_email: str) -> bool:
        """Cancel RSVP with status 'joined'"""
        return self.rsvp_service.cancel_joined_rsvp(event_id, user_email)

    def cancel_interested_rsvp(self, event_id: str, user_email: str) -> bool:
        """Cancel RSVP with status 'interested'"""
        return self.rsvp_service.cancel_interested_rsvp(event_id, user_email)

    def update_rsvp_status(self, event_id: str, user_email: str, status: str, rating: Optional[int] = None, review: Optional[str] = None) -> bool:
        """Update RSVP status and optionally set review/rating"""
        return self.rsvp_service.update_rsvp_status(event_id, user_email, status, rating, review)

    def get_rsvp_list(self, event_id: str) -> List[Dict[str, Any]]:
        """Get structured RSVP list for an event"""
        return self.rsvp_service.get_rsvp_list(event_id)

    def get_user_rsvps(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all events a user has RSVP'd to"""
        return self.rsvp_service.get_user_rsvps(user_email)

    def get_user_rsvps_paginated(self, user_email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events a user has RSVP'd to"""
        events, next_cursor = self.rsvp_service.get_user_rsvps_paginated(user_email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    def get_rsvp_statistics(self, event_id: str) -> Dict[str, Any]:
        """Get RSVP statistics for an event"""
        return self.rsvp_service.get_rsvp_statistics(event_id)

    # User Operations (delegated to EventUserRepository)
    def get_events_by_creator(self, email: str) -> List[Dict[str, Any]]:
        """Get all events created by a specific user"""
        return self.user_repo.get_events_by_creator(email)

    def get_events_by_creator_paginated(self, email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated events created by a specific user"""
        events, next_cursor = self.user_repo.get_events_by_creator_paginated(email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    def get_events_organized_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get events organized by a specific user (non-paginated)"""
        return self.user_repo.get_events_organized_by_user(user_email)

    def get_events_organized_by_user_paginated(self, user_email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated events organized by a specific user"""
        events, next_cursor = self.user_repo.get_events_organized_by_user_paginated(user_email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    def get_external_events(self, city, state):
        """Get external events for a city and state"""
        return self.query_repo.get_external_events(city, state)

    def get_external_events_paginated(self, city: str, state: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated external events for a city and state"""
        return self.query_repo.get_external_events_paginated(city, state, cursor_params)

    def get_events_moderated_by_user_paginated(self, user_email: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor paginated events moderated by a specific user"""
        events, next_cursor = self.user_repo.get_events_moderated_by_user_paginated(user_email, cursor_params)
        return events, next_cursor, None, bool(next_cursor), False

    def update_event_roles(self, event_id: str, field: str, emails: List[str]) -> bool:
        """Update event roles (organizers or moderators)"""
        return self.user_repo.update_event_roles(event_id, field, emails)

    def get_user_event_summary(self, user_email: str) -> Dict[str, Any]:
        """Get a summary of all events related to a user"""
        return self.user_repo.get_user_event_summary(user_email)
