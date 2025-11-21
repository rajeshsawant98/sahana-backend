from google.cloud.firestore_v1 import ArrayRemove
from datetime import datetime
from ..base_repository import BaseRepository
from app.models.pagination import PaginationParams, CursorPaginationParams, CursorInfo
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Optional, Dict, Any

class EventRsvpRepository(BaseRepository):
    # RSVP status setters
    async def join_rsvp(self, event_id: str, user_email: str) -> bool:
        """RSVP as joined to an event"""
        return await self._set_rsvp_status(event_id, user_email, "joined")

    async def interested_rsvp(self, event_id: str, user_email: str) -> bool:
        """RSVP as interested to an event"""
        return await self._set_rsvp_status(event_id, user_email, "interested")

    async def _set_rsvp_status(self, event_id: str, user_email: str, status: str) -> bool:
        """Helper to set RSVP status for a user, removing rating/review if not attended"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = await event_ref.get()
            if not event_doc.exists:
                self.logger.warning(f"Event {event_id} not found for RSVP")
                return False
            event_data = event_doc.to_dict()
            if event_data is None:
                self.logger.warning(f"Event {event_id} has no data")
                return False
            current_rsvps = event_data.get("rsvpList", [])
            rsvp_objs = []
            found = False
            for rsvp in current_rsvps:
                if rsvp["email"] == user_email:
                    # Only keep one RSVP per user
                    rsvp["status"] = status
                    if status == "attended":
                        # Allow rating/review only for attended
                        # Keep existing rating/review if present
                        pass
                    else:
                        rsvp.pop("rating", None)
                        rsvp.pop("review", None)
                    found = True
                    rsvp_objs.append(rsvp)
                else:
                    rsvp_objs.append(rsvp)
            if not found:
                new_rsvp = {"email": user_email, "status": status}
                rsvp_objs.append(new_rsvp)
            await event_ref.update({"rsvpList": rsvp_objs})
            self.logger.info(f"User {user_email} RSVP'd to event {event_id} as {status}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting RSVP status for user {user_email} to {status} in event {event_id}: {e}", exc_info=True)
            return False

    # RSVP cancellers
    async def cancel_joined_rsvp(self, event_id: str, user_email: str) -> bool:
        """Remove RSVP with status 'joined' for a user"""
        return await self._cancel_rsvp_by_status(event_id, user_email, "joined")

    async def cancel_interested_rsvp(self, event_id: str, user_email: str) -> bool:
        """Remove RSVP with status 'interested' for a user"""
        return await self._cancel_rsvp_by_status(event_id, user_email, "interested")

    async def _cancel_rsvp_by_status(self, event_id: str, user_email: str, status: str) -> bool:
        """Helper to remove RSVP for a user with a specific status"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = await event_ref.get()
            if not event_doc.exists:
                self.logger.warning(f"Event {event_id} not found for RSVP cancel")
                return False
            event_data = event_doc.to_dict()
            if event_data is None:
                self.logger.warning(f"Event {event_id} has no data")
                return False
            current_rsvps = event_data.get("rsvpList", [])
            rsvp_objs = []
            removed = False
            for rsvp in current_rsvps:
                # Only remove RSVP if both email and status match
                if rsvp["email"] == user_email and rsvp["status"] == status:
                    removed = True
                    continue
                rsvp_objs.append(rsvp)
            await event_ref.update({"rsvpList": rsvp_objs})
            self.logger.info(f"User {user_email} cancelled RSVP with status '{status}' for event {event_id}")
            if not removed:
                self.logger.warning(f"No RSVP found for user {user_email} with status '{status}' in event {event_id}")
            return removed
        except Exception as e:
            self.logger.error(f"Error cancelling RSVP with status '{status}' for user {user_email} from event {event_id}: {e}", exc_info=True)
            return False

    # RSVP status updater

    # RSVP getters
    """Repository for RSVP-related operations"""
    
    def __init__(self):
        super().__init__("events")
        self.logger = get_repository_logger(__name__)

    # Deprecated: use join_rsvp or interested_rsvp
    async def rsvp_to_event(self, event_id: str, user_email: str) -> bool:
        """Legacy RSVP join method (for backward compatibility)"""
        return await self.join_rsvp(event_id, user_email)

    async def cancel_rsvp(self, event_id: str, user_email: str) -> bool:
        """Remove user RSVP from an event (object-based)"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = await event_ref.get()
            if not event_doc.exists:
                self.logger.warning(f"Event {event_id} not found for RSVP cancel")
                return False
            event_data = event_doc.to_dict()
            if event_data is None:
                self.logger.warning(f"Event {event_id} has no data")
                return False
            current_rsvps = event_data.get("rsvpList", [])
            # Remove RSVP for user
            new_rsvps = [r for r in current_rsvps if r["email"] != user_email]
            await event_ref.update({"rsvpList": new_rsvps})
            self.logger.info(f"User {user_email} cancelled RSVP for event {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling RSVP for user {user_email} from event {event_id}: {e}", exc_info=True)
            return False

    async def get_rsvp_list(self, event_id: str) -> List[Dict[str, Any]]:
        """Get structured RSVP list for an event"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = await event_ref.get()
            if event_doc.exists:
                event_data = event_doc.to_dict()
                rsvp_list = event_data.get("rsvpList", []) if event_data else []
                return rsvp_list
            else:
                self.logger.warning(f"Event {event_id} not found for RSVP list")
                return []
        except Exception as e:
            self.logger.error(f"Error getting RSVP list for event {event_id}: {e}", exc_info=True)
            return []
        
        
    async def update_rsvp_status(self, event_id: str, user_email: str, status: str, rating: Optional[int] = None, review: Optional[str] = None) -> bool:
        """Update RSVP status for a user. If status is 'attended', set review and rating."""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = await event_ref.get()
            if not event_doc.exists:
                self.logger.warning(f"Event {event_id} not found for RSVP update")
                return False
            event_data = event_doc.to_dict()
            if event_data is None:
                self.logger.warning(f"Event {event_id} has no data")
                return False
            current_rsvps = event_data.get("rsvpList", [])
            rsvp_objs = []
            updated = False
            for rsvp in current_rsvps:
                if rsvp["email"] == user_email:
                    rsvp["status"] = status
                    if status == "attended":
                        if rating is not None:
                            rsvp["rating"] = str(rating)
                        if review is not None:
                            rsvp["review"] = str(review)
                    else:
                        rsvp.pop("rating", None)
                        rsvp.pop("review", None)
                    updated = True
                rsvp_objs.append(rsvp)
            if updated:
                await event_ref.update({"rsvpList": rsvp_objs})
            self.logger.info(f"User {user_email} RSVP status updated for event {event_id} to {status}")
            return updated
        except Exception as e:
            self.logger.error(f"Error updating RSVP status for user {user_email} in event {event_id}: {e}", exc_info=True)
            return False

    async def get_user_rsvps(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all events a user has RSVP'd to (object-based filtering)"""
        try:
            docs = self.collection.stream()
            events = []
            async for doc in docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    rsvp_list = event_data.get("rsvpList", [])
                    # Check if user_email is in RSVP list
                    if any(r["email"] == user_email for r in rsvp_list):
                        events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting user RSVPs for {user_email}: {e}", exc_info=True)
            return []

    async def get_user_rsvps_paginated(
        self, 
        user_email: str, 
        cursor_params: Optional[CursorPaginationParams] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get user's RSVPs using cursor-based pagination (object-based filtering).
        Orders by startTime ascending for consistent pagination.
        """
        try:
            self.logger.info(f"Getting cursor-paginated RSVPs for user: {user_email}")
            docs = self.collection.stream()
            events = []
            async for doc in docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    rsvp_list = event_data.get("rsvpList", [])
                    if any(r["email"] == user_email for r in rsvp_list):
                        event_data['eventId'] = doc.id
                        events.append(event_data)
            # Sort by startTime and eventId
            events.sort(key=lambda e: (e.get('startTime', ''), e.get('eventId', '')))
            # Pagination
            page_size = cursor_params.page_size if cursor_params else 20
            page = 1
            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info:
                    # Find start index
                    start_idx = 0
                    for i, e in enumerate(events):
                        if e.get('startTime') == getattr(cursor_info, 'start_time', None) and e.get('eventId') == getattr(cursor_info, 'event_id', None):
                            start_idx = i + 1
                            break
                    events = events[start_idx:]
            has_next_page = len(events) > page_size
            paginated_events = events[:page_size]
            next_cursor = None
            if has_next_page and paginated_events:
                last_event = paginated_events[-1]
                start_time = last_event.get('startTime')
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat()
                cursor_info = CursorInfo(
                    start_time=start_time,
                    event_id=last_event.get('eventId')
                )
                next_cursor = cursor_info.encode()
            self.logger.info(f"Retrieved {len(paginated_events)} RSVPs for user {user_email} (has_next: {has_next_page})")
            return paginated_events, next_cursor
        except Exception as e:
            self.logger.error(f"Error getting cursor-paginated RSVPs for user {user_email}: {e}")
            raise

    async def get_rsvp_statistics(self, event_id: str) -> Dict[str, Any]:
        """Get RSVP statistics for an event"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = await event_ref.get()
            
            if not event_doc.exists:
                return {"total_rsvps": 0, "rsvp_list": []}
            
            event_data = event_doc.to_dict()
            if not event_data:
                return {"total_rsvps": 0, "rsvp_list": []}
            
            rsvp_list = event_data.get("rsvpList", [])
            return {
                "total_rsvps": len(rsvp_list),
                "rsvp_list": rsvp_list
            }
        except Exception as e:
            self.logger.error(f"Error getting RSVP statistics for event {event_id}: {e}", exc_info=True)
            return {"total_rsvps": 0, "rsvp_list": []}
