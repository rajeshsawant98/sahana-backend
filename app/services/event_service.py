from app.repositories.events import EventRepositoryManager
from app.services.user_service import validate_user_emails
from app.models.pagination import EventFilters, CursorPaginationParams, EventCursorPaginatedResponse
from app.utils.logger import get_service_logger
from typing import Optional
from datetime import datetime, timedelta

event_repo = EventRepositoryManager()
logger = get_service_logger(__name__)

def create_event(data: dict):
    try:
        return event_repo.create_event(data)
    except Exception as e:
        logger.error(f"Error in create_event: {e}", exc_info=True)
        return None

def get_event_by_id(event_id: str):
    try:
        return event_repo.get_event_by_id(event_id)
    except Exception as e:
        logger.error(f"Error in get_event_by_id: {e}", exc_info=True)
        return None

def get_all_events():
    try:
        return event_repo.get_all_events()
    except Exception as e:
        logger.error(f"Error in get_all_events: {e}", exc_info=True)
        return []

def update_event(event_id: str, update_data: dict):
    try:
        return event_repo.update_event(event_id, update_data)
    except Exception as e:
        logger.error(f"Error in update_event: {e}", exc_info=True)
        return False

def delete_event(event_id: str):
    try:
        return event_repo.delete_event(event_id)
    except Exception as e:
        logger.error(f"Error in delete_event: {e}", exc_info=True)
        return False

def get_my_events(email: str):
    try:
        return event_repo.get_events_by_creator(email)
    except Exception as e:
        logger.error(f"Error in get_my_events: {e}", exc_info=True)
        return []

def rsvp_to_event(event_id: str, email: str):
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
        logger.error(f"Error in rsvp_to_event: {e}", exc_info=True)
        return False

def cancel_user_rsvp(event_id: str, email: str):
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
        logger.error(f"Error in get_user_rsvps: {e}", exc_info=True)
        return []

def get_events_organized_by_user(email: str):
    try:
        return event_repo.get_events_organized_by_user(email)
    except Exception as e:
        logger.error(f"Error in get_events_organized_by_user: {e}", exc_info=True)
        return []

def get_rsvp_list(event_id: str):
    try:
        return event_repo.get_rsvp_list(event_id)
    except Exception as e:
        logger.error(f"Error in get_rsvp_list: {e}", exc_info=True)
        return []

def get_external_events(city: str, state: str) -> list[dict]:
    try:
        return event_repo.get_external_events(city, state)
    except Exception as e:
        logger.error(f"Error in get_external_events: {e}", exc_info=True)
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
    try:
        return event_repo.archive_event(event_id, archived_by, reason)
    except Exception as e:
        logger.error(f"Error in archive_event: {e}", exc_info=True)
        return False

def unarchive_event(event_id: str) -> bool:
    try:
        return event_repo.unarchive_event(event_id)
    except Exception as e:
        logger.error(f"Error in unarchive_event: {e}", exc_info=True)
        return False

def get_archived_events(user_email: Optional[str] = None) -> list[dict]:
    try:
        return event_repo.get_archived_events(user_email)
    except Exception as e:
        logger.error(f"Error in get_archived_events: {e}", exc_info=True)
        return []

def archive_past_events(archived_by: str = "system") -> int:
    try:
        # Get all events that could potentially be archived
        events_to_check = event_repo.get_events_for_archiving()
        
        events_to_archive = []
        for event in events_to_check:
            start_time = event.get("startTime")
            duration = event.get("duration", 0)
            
            if start_time:
                try:
                    # Parse start time and calculate end time
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end_dt = start_dt + timedelta(minutes=duration)
                    
                    # If event has ended, mark for archiving
                    if end_dt < datetime.utcnow().replace(tzinfo=end_dt.tzinfo):
                        events_to_archive.append(event["documentId"])
                except Exception as parse_error:
                    logger.warning(f"Error parsing date for event {event.get('documentId')}: {parse_error}")
                    continue
        
        # Archive the identified events
        return event_repo.archive_events_by_ids(events_to_archive, archived_by)
        
    except Exception as e:
        logger.error(f"Error in archive_past_events: {e}", exc_info=True)
        return 0

def is_event_past(event: dict) -> bool:
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
        logger.error(f"Error checking if event is past: {e}", exc_info=True)
        return False

def get_all_events_paginated(cursor_params: CursorPaginationParams, filters: Optional[EventFilters] = None) -> EventCursorPaginatedResponse:
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_all_events_paginated(cursor_params, filters)
        return EventCursorPaginatedResponse.create(
            items=events,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_next,
            has_previous=has_previous,
            page_size=cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_all_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_nearby_events_paginated(city: str, state: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_nearby_events_paginated(city, state, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_nearby_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_my_events_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events created by user"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_events_by_creator_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_my_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_user_rsvps_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events user has RSVP'd to"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_user_rsvps_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_user_rsvps_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_events_organized_by_user_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events organized by user"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_events_organized_by_user_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_events_organized_by_user_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_events_moderated_by_user_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events moderated by user"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_events_moderated_by_user_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_events_moderated_by_user_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_archived_events_paginated(cursor_params: CursorPaginationParams, user_email: Optional[str] = None) -> EventCursorPaginatedResponse:
    """Get cursor-paginated archived events"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = event_repo.get_archived_events_paginated(cursor_params, user_email)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_archived_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

def get_rsvp_response_data(event_id: str, user_email: str, action: str) -> dict:
    """Get formatted RSVP response data - centralized response formatting"""
    try:
        event = get_event_by_id(event_id)
        rsvp_list = event.get("rsvpList", []) if event else []
        
        return {
            "message": f"RSVP {action} successfully",
            "rsvp_status": "going" if action == "created" else None,
            "event": {
                "id": event_id,
                "title": event.get("eventName", "") if event else "",
                "current_attendees": len(rsvp_list)
            }
        }
    except Exception as e:
        raise Exception(f"Error getting RSVP response data: {e}")

def get_paginated_rsvp_list(event_id: str, page: Optional[int] = None, page_size: int = 10) -> dict:
    """Get paginated RSVP list - centralized pagination logic"""
    try:
        rsvp_list = get_rsvp_list(event_id)
        
        if page is not None:
            # Paginated response
            total_count = len(rsvp_list)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_rsvps = rsvp_list[start_idx:end_idx]
            
            return {
                "items": [{"user_email": email} for email in paginated_rsvps],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": end_idx < total_count,
                    "has_prev": page > 1
                }
            }
        else:
            # Non-paginated response
            return {
                "rsvp_list": rsvp_list,
                "total_count": len(rsvp_list)
            }
    except Exception as e:
        raise Exception(f"Error getting paginated RSVP list: {e}")

def archive_event_with_validation(event_id: str, archived_by: str, reason: str = "Event archived") -> dict:
    """Archive event with business logic validation and response formatting"""
    try:
        # Business logic: Check if event exists
        event = get_event_by_id(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Business logic: Check if event is in the past (optional validation)
        is_past = is_event_past(event)
        
        # Perform archiving
        success = archive_event(event_id, archived_by, reason)
        if not success:
            raise Exception("Failed to archive event")
        
        # Format response with business logic
        message = "Event archived successfully"
        if not is_past:
            message += " (Note: This event has not ended yet)"
            
        return {
            "success": True,
            "message": message,
            "archived_by": archived_by,
            "reason": reason,
            "was_past_event": is_past
        }
        
    except ValueError as e:
        return {"success": False, "error": str(e), "error_type": "not_found"}
    except Exception as e:
        logger.error(f"Error in archive_event_with_validation: {e}", exc_info=True)
        return {"success": False, "error": str(e), "error_type": "server_error"}