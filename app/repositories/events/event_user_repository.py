from ..base_repository import BaseRepository
from app.models.pagination import PaginationParams, CursorPaginationParams, CursorInfo
from app.utils.logger import get_repository_logger
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

class EventUserRepository(BaseRepository):
    """Repository for user-specific event queries"""
    
    def __init__(self):
        super().__init__("events")
        self.logger = get_repository_logger(__name__)

    def get_events_by_creator(self, email: str) -> List[Dict[str, Any]]:
        """Get all events created by a specific user"""
        try:
            query = self.collection.where("createdByEmail", "==", email)
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting events by creator {email}: {e}", exc_info=True)
            return []

    def get_events_by_creator_paginated(
        self, 
        email: str, 
        cursor_params: Optional[CursorPaginationParams] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get events created by a specific user using cursor-based pagination.
        Orders by startTime ascending for consistent pagination.
        
        Args:
            email: Creator's email address
            cursor_params: Cursor pagination parameters
        
        Returns:
            Tuple of (list of events, next cursor string)
        """
        try:
            self.logger.info(f"Getting cursor-paginated events by creator: {email}")
            
            # Build base query filtering by creator and excluding archived events
            query = (self.collection
                    .where("createdByEmail", "==", email)
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
                start_time = last_event.get('startTime')
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat()
                cursor_info = CursorInfo(
                    start_time=start_time,
                    event_id=last_event.get('eventId')
                )
                next_cursor = cursor_info.encode()
            
            self.logger.info(f"Retrieved {len(events)} events by creator {email} (has_next: {has_next_page})")
            return events, next_cursor
            
        except Exception as e:
            self.logger.error(f"Error getting cursor-paginated events by creator {email}: {e}")
            raise

    def get_events_organized_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get events organized by a specific user"""
        try:
            query = self.collection.where("organizers", "array_contains", user_email)
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting events organized by user {user_email}: {e}", exc_info=True)
            return []

    def get_events_organized_by_user_paginated(
        self, 
        user_email: str, 
        cursor_params: Optional[CursorPaginationParams] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get events organized by user using cursor-based pagination"""
        try:
            query = (self.collection
                    .where("organizers", "array_contains", user_email)
                    .where("isArchived", "!=", True))
            
            query = query.order_by('startTime').order_by('eventId')
            
            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info:
                    query = query.start_after([cursor_info.start_time, cursor_info.event_id])
            
            page_size = cursor_params.page_size if cursor_params else 20
            query = query.limit(page_size + 1)
            
            results = list(query.stream())
            events = []
            has_next_page = len(results) > page_size
            
            if has_next_page:
                results = results[:-1]
            
            for doc in results:
                event_data = doc.to_dict()
                if event_data:
                    event_data['eventId'] = doc.id
                    events.append(event_data)
            
            next_cursor = None
            if has_next_page and events:
                last_event = events[-1]
                start_time = last_event.get('startTime')
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat()
                cursor_info = CursorInfo(
                    start_time=start_time,
                    event_id=last_event.get('eventId')
                )
                next_cursor = cursor_info.encode()
            
            return events, next_cursor
            
        except Exception as e:
            self.logger.error(f"Error getting cursor-paginated events organized by user {user_email}: {e}")
            raise

    def get_events_moderated_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get events moderated by a specific user"""
        try:
            query = self.collection.where("moderators", "array_contains", user_email)
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting events moderated by user {user_email}: {e}", exc_info=True)
            return []

    def get_events_moderated_by_user_paginated(
        self, 
        user_email: str, 
        cursor_params: Optional[CursorPaginationParams] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get events moderated by user using cursor-based pagination"""
        try:
            query = (self.collection
                    .where("moderators", "array_contains", user_email)
                    .where("isArchived", "!=", True))
            
            query = query.order_by('startTime').order_by('eventId')
            
            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info:
                    query = query.start_after([cursor_info.start_time, cursor_info.event_id])
            
            page_size = cursor_params.page_size if cursor_params else 20
            query = query.limit(page_size + 1)
            
            results = list(query.stream())
            events = []
            has_next_page = len(results) > page_size
            
            if has_next_page:
                results = results[:-1]
            
            for doc in results:
                event_data = doc.to_dict()
                if event_data:
                    event_data['eventId'] = doc.id
                    events.append(event_data)
            
            next_cursor = None
            if has_next_page and events:
                last_event = events[-1]
                start_time = last_event.get('startTime')
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat()
                cursor_info = CursorInfo(
                    start_time=start_time,
                    event_id=last_event.get('eventId')
                )
                next_cursor = cursor_info.encode()
            
            return events, next_cursor
            
        except Exception as e:
            self.logger.error(f"Error getting cursor-paginated events moderated by user {user_email}: {e}")
            raise

    def update_event_roles(self, event_id: str, field: str, emails: List[str]) -> bool:
        """Update event roles (organizers or moderators)"""
        try:
            event_ref = self.collection.document(event_id)
            event_ref.update({field: emails})
            return True
        except Exception as e:
            self.logger.error(f"Error updating event {event_id} {field}: {e}", exc_info=True)
            return False

    def get_user_event_summary(self, user_email: str) -> Dict[str, Any]:
        """Get a summary of all events related to a user"""
        try:
            created_events = self.get_events_by_creator(user_email)
            organized_events = self.get_events_organized_by_user(user_email)
            moderated_events = self.get_events_moderated_by_user(user_email)
            
            return {
                "created_count": len(created_events),
                "organized_count": len(organized_events),
                "moderated_count": len(moderated_events),
                "total_managed": len(created_events) + len(organized_events) + len(moderated_events)
            }
        except Exception as e:
            self.logger.error(f"Error getting user event summary for {user_email}: {e}", exc_info=True)
            return {"created_count": 0, "organized_count": 0, "moderated_count": 0, "total_managed": 0}

