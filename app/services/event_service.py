import json
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.repositories.events import EventRepositoryManager
from app.services.event_rsvp_service import EventRsvpService
from app.services.user_service import validate_user_emails
from app.models.pagination import EventFilters, CursorPaginationParams, EventCursorPaginatedResponse
from app.utils.logger import get_service_logger
from app.utils.event_validators import EventValidator
from app.utils.redis_client import get_redis_client
from app.utils.cache_keys import event_query_cache_key, nearby_events_cache_key, TTL_EVENT_QUERY
from typing import Optional
from datetime import datetime, timedelta


event_rsvp_service = EventRsvpService()

event_repo = EventRepositoryManager()
logger = get_service_logger(__name__)

async def flush_event_query_cache() -> None:
    redis = get_redis_client()
    if redis is None:
        return
    try:
        for pattern in ("sahana:events:q:*", "sahana:events:nearby:*", "sahana:search:*"):
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
    except Exception as e:
        logger.warning(f"Could not flush event query cache: {e}")


async def create_event(data: dict):
    try:
        result = await event_repo.create_event(data)
        await flush_event_query_cache()
        return result
    except Exception as e:
        logger.error(f"Error in create_event: {e}", exc_info=True)
        return None

async def get_event_by_id(event_id: str):
    try:
        return await event_repo.get_event_by_id(event_id)
    except Exception as e:
        logger.error(f"Error in get_event_by_id: {e}", exc_info=True)
        return None

async def get_all_events():
    try:
        return await event_repo.get_all_events()
    except Exception as e:
        logger.error(f"Error in get_all_events: {e}", exc_info=True)
        return []

async def update_event(event_id: str, update_data: dict):
    try:
        result = await event_repo.update_event(event_id, update_data)
        await flush_event_query_cache()
        return result
    except Exception as e:
        logger.error(f"Error in update_event: {e}", exc_info=True)
        return False

async def delete_event(event_id: str):
    try:
        result = await event_repo.delete_event(event_id)
        await flush_event_query_cache()
        return result
    except Exception as e:
        logger.error(f"Error in delete_event: {e}", exc_info=True)
        return False

async def get_my_events(email: str):
    try:
        return await event_repo.get_events_by_creator(email)
    except Exception as e:
        logger.error(f"Error in get_my_events: {e}", exc_info=True)
        return []

async def rsvp_to_event(event_id: str, email: str):
    try:
        return await event_rsvp_service.join_event(event_id, email)
    except Exception as e:
        logger.error(f"Error in rsvp_to_event: {e}", exc_info=True)
        return False

async def cancel_user_rsvp(event_id: str, email: str):
    try:
        return await event_rsvp_service.cancel_joined_rsvp(event_id, email)
    except Exception as e:
        logger.error(f"Error in cancel_user_rsvp: {e}", exc_info=True)
        raise Exception(f"Error cancelling RSVP: {e}")

async def get_user_rsvps(email: str):
    try:
        return await event_rsvp_service.get_user_rsvps(email)
    except Exception as e:
        logger.error(f"Error in get_user_rsvps: {e}", exc_info=True)
        return []

async def get_events_organized_by_user(email: str):
    try:
        return await event_repo.get_events_organized_by_user(email)
    except Exception as e:
        logger.error(f"Error in get_events_organized_by_user: {e}", exc_info=True)
        return []

async def get_rsvp_list(event_id: str):
    try:
        return await event_rsvp_service.get_rsvp_list(event_id)
    except Exception as e:
        logger.error(f"Error in get_rsvp_list: {e}", exc_info=True)
        return []

async def get_external_events(city: str, state: str) -> list[dict]:
    try:
        return await event_repo.get_external_events(city, state)
    except Exception as e:
        logger.error(f"Error in get_external_events: {e}", exc_info=True)
        return []
    
#Role assignment with email validation
async def set_organizers(event_id: str, emails: list[str], creator_email: str) -> dict:
    result = await validate_user_emails(emails)
    valid_emails = result["valid"]
    invalid_emails = result["invalid"]

    # Ensure creator is always an organizer
    if creator_email not in valid_emails:
        valid_emails.append(creator_email)

    success = await event_repo.update_event_roles(event_id, "organizers", valid_emails)
    return {
        "success": success,
        "organizers": valid_emails,
        "skipped": invalid_emails
    }

async def set_moderators(event_id: str, emails: list[str]) -> dict:
    result = await validate_user_emails(emails)
    valid_emails = result["valid"]
    invalid_emails = result["invalid"]

    success = await event_repo.update_event_roles(event_id, "moderators", valid_emails)
    return {
        "success": success,
        "moderators": valid_emails,
        "skipped": invalid_emails
    }
    

async def delete_old_events() -> int:
    return await event_repo.delete_events_before_today()

async def archive_event(event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
    try:
        result = await event_repo.archive_event(event_id, archived_by, reason)
        await flush_event_query_cache()
        return result
    except Exception as e:
        logger.error(f"Error in archive_event: {e}", exc_info=True)
        return False

async def unarchive_event(event_id: str) -> bool:
    try:
        return await event_repo.unarchive_event(event_id)
    except Exception as e:
        logger.error(f"Error in unarchive_event: {e}", exc_info=True)
        return False

async def get_archived_events(user_email: Optional[str] = None) -> list[dict]:
    try:
        return await event_repo.get_archived_events(user_email)
    except Exception as e:
        logger.error(f"Error in get_archived_events: {e}", exc_info=True)
        return []

async def archive_past_events(archived_by: str = "system") -> int:
    try:
        # Get all events that could potentially be archived
        events_to_check = await event_repo.get_events_for_archiving()
        
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
        return await event_repo.archive_events_by_ids(events_to_archive, archived_by)
        
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

async def get_all_events_paginated(cursor_params: CursorPaginationParams, filters: Optional[EventFilters] = None) -> EventCursorPaginatedResponse:
    redis = get_redis_client()
    cache_key = event_query_cache_key(
        cursor_params.model_dump() if hasattr(cursor_params, "model_dump") else vars(cursor_params),
        filters.model_dump() if filters and hasattr(filters, "model_dump") else (vars(filters) if filters else {}),
    )

    if redis is not None:
        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.debug(f"[EventCache] hit {cache_key}")
                return EventCursorPaginatedResponse(**json.loads(cached))
        except Exception:
            pass

    try:
        events, next_cursor, prev_cursor, has_next, has_previous = await event_repo.get_all_events_paginated(cursor_params, filters)
        response = EventCursorPaginatedResponse.create(
            items=events,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_next,
            has_previous=has_previous,
            page_size=cursor_params.page_size
        )

        if redis is not None:
            try:
                await redis.set(cache_key, response.model_dump_json(), ex=TTL_EVENT_QUERY)
            except Exception:
                pass

        return response
    except Exception as e:
        logger.error(f"Error in get_all_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_nearby_events_paginated(city: str, state: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    redis = get_redis_client()
    cache_key = nearby_events_cache_key(
        city, state,
        cursor_params.model_dump() if hasattr(cursor_params, "model_dump") else vars(cursor_params),
    )

    if redis is not None:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return EventCursorPaginatedResponse(**json.loads(cached))
        except Exception:
            pass

    try:
        events, next_cursor, prev_cursor, has_next, has_previous = await event_repo.get_nearby_events_paginated(city, state, cursor_params)
        response = EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
        if redis is not None:
            try:
                await redis.set(cache_key, response.model_dump_json(), ex=TTL_EVENT_QUERY)
            except Exception:
                pass
        return response
    except Exception as e:
        logger.error(f"Error in get_nearby_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_my_events_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events created by user"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = await event_repo.get_events_by_creator_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_my_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_user_rsvps_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events user has RSVP'd to"""
    try:
        events, next_cursor = await event_rsvp_service.get_user_rsvps_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            items=events,
            next_cursor=next_cursor,
            prev_cursor=None,
            has_next=bool(next_cursor),
            has_previous=False,
            page_size=cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_user_rsvps_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_events_organized_by_user_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events organized by user"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = await event_repo.get_events_organized_by_user_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_events_organized_by_user_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_user_interested_events_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events user has RSVP'd as 'interested'"""
    try:
        events, next_cursor = await event_rsvp_service.get_user_rsvps_paginated(email, cursor_params, status="interested")
        return EventCursorPaginatedResponse.create(
            items=events,
            next_cursor=next_cursor,
            prev_cursor=None,
            has_next=bool(next_cursor),
            has_previous=False,
            page_size=cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_user_interested_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_events_moderated_by_user_paginated(email: str, cursor_params: CursorPaginationParams) -> EventCursorPaginatedResponse:
    """Get cursor-paginated events moderated by user"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = await event_repo.get_events_moderated_by_user_paginated(email, cursor_params)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_events_moderated_by_user_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_archived_events_paginated(cursor_params: CursorPaginationParams, user_email: Optional[str] = None) -> EventCursorPaginatedResponse:
    """Get cursor-paginated archived events"""
    try:
        events, next_cursor, prev_cursor, has_next, has_previous = await event_repo.get_archived_events_paginated(cursor_params, user_email)
        return EventCursorPaginatedResponse.create(
            events, next_cursor, prev_cursor, has_next, has_previous, cursor_params.page_size
        )
    except Exception as e:
        logger.error(f"Error in get_archived_events_paginated: {e}", exc_info=True)
        return EventCursorPaginatedResponse.create([], None, None, False, False, cursor_params.page_size)

async def get_rsvp_response_data(event_id: str, user_email: str, action: str) -> dict:
    """Lightweight RSVP response — fetches only event name + RSVP count."""
    event_name, rsvp_count = "", 0
    try:
        async with AsyncSessionLocal() as session:
            row = await session.execute(
                text("SELECT event_name FROM events WHERE event_id = :eid"),
                {"eid": event_id}
            )
            r = row.fetchone()
            if r:
                event_name = r.event_name
        rsvp_count = await event_rsvp_service.repo.get_rsvp_count(event_id)
    except Exception:
        pass
    return {
        "message": f"RSVP {action} successfully",
        "rsvp_status": "going" if action == "created" else None,
        "event": {
            "id": event_id,
            "title": event_name,
            "current_attendees": rsvp_count,
        }
    }

async def get_paginated_rsvp_list(event_id: str, page: int = 1, page_size: int = 10) -> dict:
    """Get paginated RSVP list for an event — count and items fetched separately from DB."""
    offset = (page - 1) * page_size
    try:
        async with AsyncSessionLocal() as session:
            total_count = int(await session.scalar(
                text("SELECT COUNT(*) FROM rsvps WHERE event_id = :eid"),
                {"eid": event_id}
            ) or 0)
            result = await session.execute(text("""
                SELECT user_email, status, rating, review
                FROM rsvps WHERE event_id = :eid
                ORDER BY updated_at DESC
                LIMIT :limit OFFSET :offset
            """), {"eid": event_id, "limit": page_size, "offset": offset})
            items = [
                {"email": r.user_email, "status": r.status,
                 **({"rating": r.rating} if r.rating is not None else {}),
                 **({"review": r.review} if r.review is not None else {})}
                for r in result.fetchall()
            ]
    except Exception as e:
        logger.error(f"Error in get_paginated_rsvp_list: {e}", exc_info=True)
        total_count, items = 0, []
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": offset + page_size < total_count,
            "has_prev": page > 1,
        }
    }

async def archive_event_with_validation(event_id: str, archived_by: str, reason: str = "Event archived") -> dict:
    """Archive event with business logic validation and response formatting"""
    try:
        # Business logic: Check if event exists
        event = await get_event_by_id(event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Business logic: Check if event is in the past (optional validation)
        is_past = is_event_past(event)
        
        # Perform archiving
        success = await archive_event(event_id, archived_by, reason)
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