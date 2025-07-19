from google.cloud.firestore_v1 import ArrayRemove
from ..base_repository import BaseRepository
from app.models.pagination import PaginationParams, CursorPaginationParams, CursorInfo
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Optional, Dict, Any

class EventRsvpRepository(BaseRepository):
    """Repository for RSVP-related operations"""
    
    def __init__(self):
        super().__init__("events")
        self.logger = get_repository_logger(__name__)

    def rsvp_to_event(self, event_id: str, user_email: str) -> bool:
        """Add user RSVP to an event"""
        try:
            event_ref = self.collection.document(event_id)
            
            # Check if event exists first
            event_doc = event_ref.get()
            if not event_doc.exists:
                self.logger.warning(f"Event {event_id} not found for RSVP")
                return False
            
            event_data = event_doc.to_dict()
            if event_data is None:
                self.logger.warning(f"Event {event_id} has no data")
                return False
            
            # Add user to RSVP list
            current_rsvps = event_data.get("rsvpList", [])
            if user_email not in current_rsvps:
                event_ref.update({
                    "rsvpList": current_rsvps + [user_email]
                })
            
            self.logger.info(f"User {user_email} RSVP'd to event {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding RSVP for user {user_email} to event {event_id}: {e}", exc_info=True)
            return False

    def cancel_rsvp(self, event_id: str, user_email: str) -> bool:
        """Remove user RSVP from an event"""
        try:
            event_ref = self.collection.document(event_id)
            event_ref.update({
                "rsvpList": ArrayRemove([user_email])
            })
            self.logger.info(f"User {user_email} cancelled RSVP for event {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling RSVP for user {user_email} from event {event_id}: {e}", exc_info=True)
            return False

    def get_rsvp_list(self, event_id: str) -> List[str]:
        """Get list of users who RSVP'd to an event"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = event_ref.get()
            
            if event_doc.exists:
                event_data = event_doc.to_dict()
                return event_data.get("rsvpList", []) if event_data else []
            else:
                self.logger.warning(f"Event {event_id} not found for RSVP list")
                return []
        except Exception as e:
            self.logger.error(f"Error getting RSVP list for event {event_id}: {e}", exc_info=True)
            return []

    def get_user_rsvps(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all events a user has RSVP'd to"""
        try:
            query = self.collection.where("rsvpList", "array_contains", user_email)
            
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting user RSVPs for {user_email}: {e}", exc_info=True)
            return []

    def get_user_rsvps_paginated(
        self, 
        user_email: str, 
        cursor_params: Optional[CursorPaginationParams] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get user's RSVPs using cursor-based pagination.
        Orders by startTime ascending for consistent pagination.
        
        Args:
            user_email: User's email for filtering RSVPs
            cursor_params: Cursor pagination parameters
        
        Returns:
            Tuple of (list of events, next cursor string)
        """
        try:
            self.logger.info(f"Getting cursor-paginated RSVPs for user: {user_email}")
            
            # Build base query filtering by user's RSVP and excluding archived events
            query = (self.collection
                    .where("rsvpList", "array_contains", user_email)
                    .where("isArchived", "!=", True))
            
            # Apply sorting and cursor positioning
            query = query.order_by('startTime').order_by('eventId')
            
            # Handle cursor positioning
            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info:
                    query = query.start_after([cursor_info.start_time, cursor_info.event_id])
            
            # Apply limit
            page_size = cursor_params.page_size if cursor_params else 20
            query = query.limit(page_size + 1)  # Fetch one extra to check for next page
            
            # Execute query
            results = list(query.stream())
            
            # Process results
            events = []
            has_next_page = len(results) > page_size
            
            # If we have more results than limit, remove the extra one
            if has_next_page:
                results = results[:-1]
            
            # Convert documents to dictionaries
            for doc in results:
                event_data = doc.to_dict()
                if event_data:  # Ensure event_data is not None
                    event_data['eventId'] = doc.id
                    events.append(event_data)
            
            # Generate cursor for next page
            next_cursor = None
            if has_next_page and events:
                last_event = events[-1]
                cursor_info = CursorInfo(
                    start_time=last_event.get('startTime'),
                    event_id=last_event.get('eventId')
                )
                next_cursor = cursor_info.encode()
            
            self.logger.info(f"Retrieved {len(events)} RSVPs for user {user_email} (has_next: {has_next_page})")
            return events, next_cursor
            
        except Exception as e:
            self.logger.error(f"Error getting cursor-paginated RSVPs for user {user_email}: {e}")
            raise

    def get_rsvp_statistics(self, event_id: str) -> Dict[str, Any]:
        """Get RSVP statistics for an event"""
        try:
            event_ref = self.collection.document(event_id)
            event_doc = event_ref.get()
            
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
