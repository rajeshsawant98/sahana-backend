from datetime import datetime
from google.cloud.firestore_v1 import Query, CollectionReference
from ..base_repository import BaseRepository
from app.models.pagination import PaginationParams, CursorPaginationParams, CursorInfo
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Optional, Dict, Any

class EventArchiveRepository(BaseRepository):
    """Repository for event archiving and archive management operations"""
    
    def __init__(self):
        super().__init__("events")
        self.logger = get_repository_logger(__name__)

    def archive_event(self, event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
        """Archive a single event"""
        try:
            event_ref = self.collection.document(event_id)
            event_ref.update({
                "isArchived": True,
                "archivedAt": datetime.now(),
                "archivedBy": archived_by,
                "archiveReason": reason
            })
            self.logger.info(f"Event {event_id} archived by {archived_by}")
            return True
        except Exception as e:
            self.logger.error(f"Error archiving event {event_id}: {e}", exc_info=True)
            return False

    def unarchive_event(self, event_id: str) -> bool:
        """Unarchive a single event"""
        try:
            event_ref = self.collection.document(event_id)
            event_ref.update({
                "isArchived": False,
                "unarchivedAt": datetime.now(),
                "archivedAt": None,
                "archivedBy": None,
                "archiveReason": None
            })
            self.logger.info(f"Event {event_id} unarchived")
            return True
        except Exception as e:
            self.logger.error(f"Error unarchiving event {event_id}: {e}", exc_info=True)
            return False

    def archive_events_by_ids(self, event_ids: List[str], archived_by: str, reason: str = "Automatically archived - event ended") -> int:
        """Archive multiple events by their IDs"""
        archived_count = 0
        try:
            for event_id in event_ids:
                if self.archive_event(event_id, archived_by, reason):
                    archived_count += 1
            
            self.logger.info(f"Archived {archived_count} events")
            return archived_count
        except Exception as e:
            self.logger.error(f"Error bulk archiving events: {e}", exc_info=True)
            return archived_count

    def get_archived_events(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all archived events, optionally filtered by user"""
        try:
            # Use single filter approach to avoid Firestore issues
            if user_email:
                # If filtering by user, start with that filter
                query = self.collection.where("createdByEmail", "==", user_email)
                
                # Get all docs and filter for archived events in Python
                docs = query.stream()
                events = []
                for doc in docs:
                    event_data = doc.to_dict()
                    if event_data and event_data.get("isArchived") == True:
                        events.append(event_data)
            else:
                # If not filtering by user, filter by archived status only
                query = self.collection.where("isArchived", "==", True)
                
                docs = query.stream()
                events = []
                for doc in docs:
                    event_data = doc.to_dict()
                    if event_data:
                        events.append(event_data)
            
            # Sort by archived date in Python (most recent first)
            events.sort(key=lambda x: x.get("archivedAt", ""), reverse=True)
            
            return events
        except Exception as e:
            self.logger.error(f"Error getting archived events: {e}", exc_info=True)
            return []

    def get_archived_events_paginated(
        self, 
        cursor_params: Optional[CursorPaginationParams] = None,
        user_email: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get archived events using cursor-based pagination.
        Orders by archivedAt descending (most recent first) for consistent pagination.
        
        Args:
            cursor_params: Cursor pagination parameters
            user_email: Optional filter by user who created the events
        
        Returns:
            Tuple of (list of archived events, next cursor string)
        """
        try:
            self.logger.info(f"Getting cursor-paginated archived events (user: {user_email})")
            
            # Build base query for archived events
            query = self.collection.where("isArchived", "==", True)
            
            # Add user filter if specified
            if user_email:
                query = query.where("createdByEmail", "==", user_email)
            
            # Apply sorting - using archivedAt descending (most recent first)
            query = query.order_by('archivedAt', direction=Query.DESCENDING).order_by('eventId')
            
            # Handle cursor positioning
            if cursor_params and cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if cursor_info:
                    # For archived events, start_time represents archivedAt
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
                archived_at = last_event.get('archivedAt')
                if isinstance(archived_at, datetime):
                    archived_at = archived_at.isoformat()
                cursor_info = CursorInfo(
                    start_time=archived_at,  # Use archivedAt for cursor
                    event_id=last_event.get('eventId')
                )
                next_cursor = cursor_info.encode()
            
            self.logger.info(f"Retrieved {len(events)} archived events (has_next: {has_next_page})")
            return events, next_cursor
            
        except Exception as e:
            self.logger.error(f"Error getting cursor-paginated archived events: {e}")
            raise

    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get statistics about archived events"""
        try:
            # Count all archived events
            archived_query = self.collection.where("isArchived", "==", True)
            archived_docs = archived_query.get()
            total_archived = len(archived_docs)
            
            # Count archived events by month (last 12 months)
            monthly_counts = {}
            for doc in archived_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("archivedAt"):
                    archived_at = event_data["archivedAt"]
                    if hasattr(archived_at, 'strftime'):
                        month_key = archived_at.strftime("%Y-%m")
                        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
            return {
                "total_archived": total_archived,
                "monthly_archived": monthly_counts
            }
        except Exception as e:
            self.logger.error(f"Error getting archive statistics: {e}", exc_info=True)
            return {"total_archived": 0, "monthly_archived": {}}
