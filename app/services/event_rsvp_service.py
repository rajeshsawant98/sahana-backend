from app.repositories.events.event_rsvp_repository import EventRsvpRepository
from app.utils.logger import get_service_logger
from app.utils.event_validators import EventValidator
from app.models.pagination import CursorPaginationParams
from typing import Optional, List, Dict, Any

class EventRsvpService:
    """Service for RSVP-related operations"""
    def __init__(self):
        self.repo = EventRsvpRepository()
        self.logger = get_service_logger(__name__)

    async def join_event(self, event_id: str, user_email: str) -> bool:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        EventValidator.validate_event_exists(event)
        EventValidator.validate_rsvp_preconditions(event, user_email)
        return await self.repo.join_rsvp(event_id, user_email)

    async def interested_in_event(self, event_id: str, user_email: str) -> bool:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        EventValidator.validate_event_exists(event)
        EventValidator.validate_rsvp_preconditions(event, user_email)
        return await self.repo.interested_rsvp(event_id, user_email)

    async def cancel_joined_rsvp(self, event_id: str, user_email: str) -> bool:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        EventValidator.validate_event_exists(event)
        EventValidator.validate_cancel_rsvp_preconditions(event, user_email)
        return await self.repo.cancel_joined_rsvp(event_id, user_email)

    async def cancel_interested_rsvp(self, event_id: str, user_email: str) -> bool:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        EventValidator.validate_event_exists(event)
        EventValidator.validate_cancel_rsvp_preconditions(event, user_email)
        return await self.repo.cancel_interested_rsvp(event_id, user_email)

    async def update_rsvp_status(self, event_id: str, user_email: str, status: str, rating: Optional[int] = None, review: Optional[str] = None) -> bool:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        EventValidator.validate_event_exists(event)
        # Only allow review/rating for attended status
        if status == "attended":
            return await self.repo.update_rsvp_status(event_id, user_email, status, rating, review)
        else:
            return await self.repo.update_rsvp_status(event_id, user_email, status)

    async def get_rsvp_list(self, event_id: str) -> List[Dict[str, Any]]:
        return await self.repo.get_rsvp_list(event_id)

    async def get_user_rsvps(self, user_email: str) -> List[Dict[str, Any]]:
        return await self.repo.get_user_rsvps(user_email)

    async def get_user_rsvps_paginated(self, user_email: str, cursor_params: Optional[CursorPaginationParams] = None):
        return await self.repo.get_user_rsvps_paginated(user_email, cursor_params)

    async def get_rsvp_statistics(self, event_id: str) -> Dict[str, Any]:
        return await self.repo.get_rsvp_statistics(event_id)
