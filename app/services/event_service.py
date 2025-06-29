from app.repositories.event_repository import EventRepository
from app.services.user_service import validate_user_emails
from app.models.pagination import PaginationParams, EventPaginatedResponse, EventFilters, PaginatedResponse
from typing import Optional
from datetime import datetime, timedelta

event_repo = EventRepository()

def create_event(data: dict):
    try:
        return event_repo.create_event(data)
    except Exception as e:
        print(f"Error in create_event: {e}")
        return None

def get_event_by_id(event_id: str):
    try:
        return event_repo.get_event_by_id(event_id)
    except Exception as e:
        print(f"Error in get_event_by_id: {e}")
        return None

def get_all_events():
    try:
        return event_repo.get_all_events()
    except Exception as e:
        print(f"Error in get_all_events: {e}")
        return []

def update_event(event_id: str, update_data: dict):
    try:
        return event_repo.update_event(event_id, update_data)
    except Exception as e:
        print(f"Error in update_event: {e}")
        return False

def delete_event(event_id: str):
    try:
        return event_repo.delete_event(event_id)
    except Exception as e:
        print(f"Error in delete_event: {e}")
        return False

def get_my_events(email: str):
    try:
        return event_repo.get_events_by_creator(email)
    except Exception as e:
        print(f"Error in get_my_events: {e}")
        return []

def rsvp_to_event(event_id: str, email: str):
    """RSVP to event with business logic validation"""
    try:
        # Check if event exists
        event = event_repo.get_event_by_id(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Check if event is archived
        if event.get("isArchived", False):
            raise ValueError("Cannot RSVP to archived event")
        
        # Check if user is already RSVP'd
        rsvp_list = event.get("rsvpList", [])
        if email in rsvp_list:
            raise ValueError("You have already RSVP'd to this event")
        
        # Perform RSVP
        return event_repo.rsvp_to_event(event_id, email)
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        print(f"Error in rsvp_to_event: {e}")
        return False

def cancel_user_rsvp(event_id: str, email: str):
    """Cancel RSVP with business logic validation"""
    try:
        # Check if event exists
        event = event_repo.get_event_by_id(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Check if user has RSVP'd
        rsvp_list = event.get("rsvpList", [])
        if email not in rsvp_list:
            raise ValueError("You have not RSVP'd to this event")
        
        # Cancel RSVP
        return event_repo.cancel_rsvp(event_id, email)
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        raise Exception(f"Error cancelling RSVP: {e}")

def get_user_rsvps(email: str):
    try:
        return event_repo.get_user_rsvps(email)
    except Exception as e:
        print(f"Error in get_user_rsvps: {e}")
        return []

def get_events_organized_by_user(email: str):
    try:
        return event_repo.get_events_organized_by_user(email)
    except Exception as e:
        print(f"Error in get_events_organized_by_user: {e}")
        return []

def get_events_moderated_by_user(email: str):
    try:
        return event_repo.get_events_moderated_by_user(email)
    except Exception as e:
        print(f"Error in get_events_moderated_by_user: {e}")
        return []   


def get_rsvp_list(event_id: str):
    try:
        return event_repo.get_rsvp_list(event_id)
    except Exception as e:
        print(f"Error in get_rsvp_list: {e}")
        return []

def get_nearby_events(city: str, state: str):
    try:
        return event_repo.get_nearby_events(city, state)
    except Exception as e:
        print(f"Error in get_nearby_events: {e}")
        return []

def get_external_events(city: str, state: str) -> list[dict]:
    try:
        return event_repo.get_external_events(city, state)
    except Exception as e:
        print(f"Error in get_external_events: {e}")
        return []
    
#Role assignment with email validation
def set_organizers(event_id: str, emails: list[str], creator_email: str) -> dict:
    result = validate_user_emails(emails)
    valid_emails = result["valid"]
    invalid_emails = result["invalid"]

    # Ensure creator is always an organizer
    if creator_email not in valid_emails:
        valid_emails.append(creator_email)

    success = event_repo.update_event_roles(event_id, "organizers", valid_emails)
    return {
        "success": success,
        "organizers": valid_emails,
        "skipped": invalid_emails
    }

def set_moderators(event_id: str, emails: list[str]) -> dict:
    result = validate_user_emails(emails)
    valid_emails = result["valid"]
    invalid_emails = result["invalid"]

    success = event_repo.update_event_roles(event_id, "moderators", valid_emails)
    return {
        "success": success,
        "moderators": valid_emails,
        "skipped": invalid_emails
    }
    

def delete_old_events() -> int:
    return event_repo.delete_events_before_today()

def archive_event(event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
    """Archive/soft delete an event"""
    try:
        return event_repo.archive_event(event_id, archived_by, reason)
    except Exception as e:
        print(f"Error in archive_event: {e}")
        return False

def unarchive_event(event_id: str) -> bool:
    """Restore an archived event"""
    try:
        return event_repo.unarchive_event(event_id)
    except Exception as e:
        print(f"Error in unarchive_event: {e}")
        return False

def get_archived_events(user_email: Optional[str] = None) -> list[dict]:
    """Get archived events, optionally filtered by creator"""
    try:
        return event_repo.get_archived_events(user_email)
    except Exception as e:
        print(f"Error in get_archived_events: {e}")
        return []

def get_archived_events_paginated(pagination: PaginationParams, user_email: Optional[str] = None) -> PaginatedResponse:
    """Get paginated archived events, optionally filtered by creator"""
    try:
        events, total_count = event_repo.get_archived_events_paginated(pagination, user_email)
        return PaginatedResponse.create(
            items=events,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        print(f"Error in get_archived_events_paginated: {e}")
        return PaginatedResponse.create(items=[], total_count=0, page=1, page_size=pagination.page_size)

def archive_past_events(archived_by: str = "system") -> int:
    """Archive all past events that have ended"""
    try:
        return event_repo.archive_past_events(archived_by)
    except Exception as e:
        print(f"Error in archive_past_events: {e}")
        return 0

def is_event_past(event: dict) -> bool:
    """Check if an event is in the past"""
    try:
        start_time = event.get("startTime")
        if not start_time:
            return False
        
        duration = event.get("duration", 0)
        
        # Parse start time and calculate end time
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = start_dt + timedelta(minutes=duration)
        
        # Check if event has ended
        return end_dt < datetime.utcnow().replace(tzinfo=end_dt.tzinfo)
    except Exception as e:
        print(f"Error checking if event is past: {e}")
        return False

def get_all_events_paginated(pagination: PaginationParams, filters: Optional[EventFilters] = None) -> EventPaginatedResponse:
    """Get paginated events with optional filters"""
    try:
        events, total_count = event_repo.get_all_events_paginated(pagination, filters)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_all_events_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)

def get_my_events_paginated(email: str, pagination: PaginationParams) -> EventPaginatedResponse:
    """Get paginated events created by user"""
    try:
        events, total_count = event_repo.get_events_by_creator_paginated(email, pagination)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_my_events_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)

def get_user_rsvps_paginated(email: str, pagination: PaginationParams) -> EventPaginatedResponse:
    """Get paginated events user has RSVP'd to"""
    try:
        events, total_count = event_repo.get_user_rsvps_paginated(email, pagination)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_user_rsvps_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)

def get_events_organized_by_user_paginated(email: str, pagination: PaginationParams) -> EventPaginatedResponse:
    """Get paginated events organized by user"""
    try:
        events, total_count = event_repo.get_events_organized_by_user_paginated(email, pagination)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_events_organized_by_user_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)

def get_events_moderated_by_user_paginated(email: str, pagination: PaginationParams) -> EventPaginatedResponse:
    """Get paginated events moderated by user"""
    try:
        events, total_count = event_repo.get_events_moderated_by_user_paginated(email, pagination)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_events_moderated_by_user_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)

def get_nearby_events_paginated(city: str, state: str, pagination: PaginationParams) -> EventPaginatedResponse:
    """Get paginated nearby events"""
    try:
        events, total_count = event_repo.get_nearby_events_paginated(city, state, pagination)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_nearby_events_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)

def get_external_events_paginated(city: str, state: str, pagination: PaginationParams) -> EventPaginatedResponse:
    """Get paginated external events"""
    try:
        events, total_count = event_repo.get_external_events_paginated(city, state, pagination)
        return EventPaginatedResponse.create(events, total_count, pagination.page, pagination.page_size)
    except Exception as e:
        print(f"Error in get_external_events_paginated: {e}")
        return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)