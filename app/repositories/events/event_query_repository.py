from datetime import datetime, timedelta
from google.cloud.firestore_v1 import Query, CollectionReference
from ..base_repository import BaseRepository
from app.models.pagination import EventFilters, CursorPaginationParams, CursorInfo
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Optional, Union, Dict, Any

class EventQueryRepository(BaseRepository):
    """Repository for complex event queries and filtering operations"""
    
    def __init__(self):
        super().__init__("events")
        self.logger = get_repository_logger(__name__)

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all non-archived events"""
        try:
            query = self.collection.limit(1000000)  # Start with collection query
            query = self._apply_non_archived_filter(query)
            query = self._apply_sorting(query)
            docs = query.get()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data is not None:
                    # Also filter out events without isArchived field (treat as non-archived)
                    if event_data.get("isArchived") != True:
                        events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting all events: {e}", exc_info=True)
            return []

    def get_nearby_events(self, city: str, state: str) -> List[Dict[str, Any]]:
        """Get events in a specific city and state (both manual and external)"""
        try:
            # Use single filter approach to avoid Firestore inequality limitations
            query = self.collection.where("location.city", "==", city)
            
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if (event_data is not None and 
                    event_data.get("isArchived") != True and
                    (event_data.get("origin") in ["manual", "external"]) and  # Include both manual and external
                    (not state or event_data.get("location", {}).get("state") == state)):
                    events.append(event_data)
            
            # Sort by start time in Python
            events.sort(key=lambda x: x.get("startTime", ""))
            return events
        except Exception as e:
            self.logger.error(f"Error getting nearby events: {e}", exc_info=True)
            return []

    def get_external_events(self, city: str, state: str) -> List[Dict[str, Any]]:
        """Get external (scraped) events in a specific city and state"""
        try:
            # Use single filter approach to avoid Firestore inequality limitations
            query = self.collection.where("location.city", "==", city)
            
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if (event_data is not None and 
                    event_data.get("isArchived") != True and
                    event_data.get("origin") == "external" and  # Changed from "scraped" to "external"
                    (not state or event_data.get("location", {}).get("state") == state)):
                    events.append(event_data)
            
            # Sort by start time in Python
            events.sort(key=lambda x: x.get("startTime", ""))
            
            return events
        except Exception as e:
            self.logger.error(f"Error getting external events: {e}", exc_info=True)
            return []

    def get_events_for_archiving(self) -> List[Dict[str, Any]]:
        """Get events that should be archived (ended events)"""
        try:
            # Fetch all non-archived events (let service filter which are past)
            query = self.collection.where("isArchived", "!=", True)
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data is not None:
                    event_data["eventId"] = doc.id
                    event_data["documentId"] = doc.id
                    events.append(event_data)
            return events
        except Exception as e:
            self.logger.error(f"Error getting events for archiving: {e}", exc_info=True)
            return []

    def delete_events_before_today(self) -> int:
        """Delete events that ended before today (for cleanup purposes)"""
        try:
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            # Get events that ended before today
            query = self.collection.where("endTime", "<", today_start)
            docs = query.get()
            
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
                
            self.logger.info(f"Deleted {deleted_count} old events")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error deleting old events: {e}", exc_info=True)
            return 0

    def get_all_events_paginated(self, cursor_params: CursorPaginationParams, 
                                       filters: Optional[EventFilters] = None) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events with filters and startTime sorting"""
        try:
            # Parse cursor
            cursor_info = None
            if cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if not cursor_info:
                    raise ValueError("Invalid cursor format")
            
            # Build query for paginated results
            query = self.collection.limit(1000000)
            query = self._apply_non_archived_filter(query)
            
            # Apply cursor-based filtering and sorting
            query = self._apply_cursor_filters(query, cursor_info, cursor_params.direction)
            query = self._apply_cursor_sorting(query)
            
            # Apply database-level filters using intelligent index selection
            query = self._apply_event_filters_with_index_selection(query, filters)
            
            # Fetch items with appropriate limits
            if cursor_info:
                fetch_limit = min(cursor_params.page_size * 3, 100)
            else:
                fetch_limit = cursor_params.page_size + 1
            
            query = query.limit(fetch_limit)
            
            # Execute query
            docs = list(query.get())
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and not event_data.get("isArchived", False):
                    event_data["eventId"] = doc.id  # Include document ID
                    events.append(event_data)
            
            # Apply cursor filtering in application layer for exact cursor position
            if cursor_info:
                events = self._filter_events_by_cursor(events, cursor_info, cursor_params.direction)
            
            # Handle backward pagination properly
            if cursor_params.direction == "prev":
                # For backward pagination, we need to:
                # 1. Get events that come before the cursor
                # 2. Take the last N events (closest to cursor)
                # 3. Return them in normal ascending order
                
                # Events are already filtered to be before cursor position
                # Now take the last page_size events (those closest to cursor)
                # but first we need to determine has_more before trimming
                has_more = len(events) > cursor_params.page_size
                
                if len(events) > cursor_params.page_size:
                    # Take the last page_size events (closest to cursor)
                    events = events[-cursor_params.page_size:]
                
                # Events are now in the correct order for display
            else:
                # Forward pagination - normal trimming
                has_more = len(events) > cursor_params.page_size
                if has_more:
                    events = events[:cursor_params.page_size]  # Remove extra items
            
            # For cursor-based pagination, has_next/has_previous logic:
            # - For forward pagination: has_next = has_more, has_previous = cursor exists
            # - For backward pagination: has_next = cursor exists, has_previous = has_more
            if cursor_params.direction == "next":
                has_next = has_more
                has_previous = cursor_params.cursor is not None
            else:  # direction == "prev"
                has_next = cursor_params.cursor is not None
                has_previous = has_more
            
            # Generate cursors
            next_cursor = None
            prev_cursor = None
            
            if events:
                first_event = events[0]
                last_event = events[-1]
                
                if has_next:
                    next_cursor = CursorInfo(
                        start_time=last_event["startTime"],
                        event_id=last_event["eventId"]
                    ).encode()
                
                if has_previous:
                    prev_cursor = CursorInfo(
                        start_time=first_event["startTime"], 
                        event_id=first_event["eventId"]
                    ).encode()
            
            return events, next_cursor, prev_cursor, has_next, has_previous
            
        except Exception as e:
            self.logger.error(f"Error in cursor pagination: {e}", exc_info=True)
            return [], None, None, False, False

    def _filter_events_by_cursor(self, events: List[Dict[str, Any]], cursor_info: CursorInfo, direction: str) -> List[Dict[str, Any]]:
        """Filter events by cursor position in application layer for exact positioning"""
        filtered_events = []
        
        def compare_start_times(event_time, cursor_time):
            """Compare startTime values, handling None cases properly"""
            # None values come first in Firestore sort order
            if event_time is None and cursor_time is None:
                return 0  # Equal
            elif event_time is None:
                return -1  # Event time is less (comes first)
            elif cursor_time is None:
                return 1  # Event time is greater (comes after)
            else:
                # Both are strings, normal comparison
                if event_time < cursor_time:
                    return -1
                elif event_time > cursor_time:
                    return 1
                else:
                    return 0
        
        for event in events:
            event_start_time = event.get("startTime")  # Don't default to ""
            event_id = event.get("eventId", "")
            
            if direction == "next":
                # Include events that are strictly after cursor position
                time_cmp = compare_start_times(event_start_time, cursor_info.start_time)
                if (time_cmp > 0 or (time_cmp == 0 and event_id > cursor_info.event_id)):
                    filtered_events.append(event)
            else:  # direction == "prev"
                # Include events that are strictly before cursor position
                time_cmp = compare_start_times(event_start_time, cursor_info.start_time)
                if (time_cmp < 0 or (time_cmp == 0 and event_id < cursor_info.event_id)):
                    filtered_events.append(event)
        
        return filtered_events

    def _apply_event_filters_with_index_selection(self, query: Query, filters: Optional[EventFilters] = None) -> Query:
        """Apply event filters using intelligent index selection to avoid missing index errors"""
        if not filters:
            return query
        
        # Strategy: Apply filters in order of available composite indexes
        # This ensures we use existing indexes and avoid "requires an index" errors
        
        # Priority 1: Location filters (city + state) - Use existing indexes when possible
        if filters.city and filters.state:
            # Use existing: location.city + location.state + startTime + isArchived index (close match)
            query = query.where("location.city", "==", filters.city)
            query = query.where("location.state", "==", filters.state)
        elif filters.state:
            # Uses existing: isArchived + location.state + startTime index ✅
            query = query.where("location.state", "==", filters.state)
        elif filters.city:
            # Note: Need to create isArchived + location.city + startTime + __name__ index
            # For now, this will fail with missing index error - user needs to create index
            query = query.where("location.city", "==", filters.city)
        
        # Priority 2: Online status filter  
        if filters.is_online is not None:
            # Uses existing: isArchived + isOnline + startTime index ✅
            query = query.where("isOnline", "==", filters.is_online)
        
        # Priority 3: Creator email filter
        if filters.creator_email:
            # Uses existing: createdByEmail + isArchived + startTime index ✅
            query = query.where("createdByEmail", "==", filters.creator_email)
        
        # Priority 4: Category filter - Will need index creation
        if filters.category:
            # Note: Need to create isArchived + categories + startTime + __name__ index
            # For now, this will fail with missing index error - user needs to create index
            query = query.where("categories", "array_contains", filters.category)
        
        # Priority 5: Date range filters (these work with existing startTime indexes)
        if filters.start_date:
            query = query.where("startTime", ">=", filters.start_date)
        if filters.end_date:
            query = query.where("startTime", "<=", filters.end_date)
        
        return query

    def get_nearby_events_paginated(self, city: str, state: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated events in a specific city and state with intelligent filtering"""
        try:
            # Parse cursor
            cursor_info = None
            if cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if not cursor_info:
                    raise ValueError("Invalid cursor format")
            
            # Build query with location filters
            query = self.collection.limit(1000000)
            query = self._apply_non_archived_filter(query)
            query = query.where("location.city", "==", city)
            if state:
                query = query.where("location.state", "==", state)
            
            # Apply cursor-based filtering and sorting
            query = self._apply_cursor_filters(query, cursor_info, cursor_params.direction)
            query = self._apply_cursor_sorting(query)
            
            # Fetch items with appropriate limits
            fetch_limit = cursor_params.page_size + 1
            if cursor_info:
                fetch_limit = min(cursor_params.page_size * 3, 100)
            
            query = query.limit(fetch_limit)
            
            # Execute query
            docs = list(query.get())
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and not event_data.get("isArchived", False):
                    event_data["eventId"] = doc.id
                    events.append(event_data)
            
            # Apply cursor filtering for exact positioning
            if cursor_info:
                events = self._filter_events_by_cursor(events, cursor_info, cursor_params.direction)
            
            # Handle pagination logic
            if cursor_params.direction == "prev":
                has_more = len(events) > cursor_params.page_size
                if has_more:
                    events = events[-cursor_params.page_size:]
                has_next = cursor_params.cursor is not None
                has_previous = has_more
            else:
                has_more = len(events) > cursor_params.page_size
                if has_more:
                    events = events[:cursor_params.page_size]
                has_next = has_more
                has_previous = cursor_params.cursor is not None
            
            # Generate cursors
            next_cursor = None
            prev_cursor = None
            
            if events:
                first_event = events[0]
                last_event = events[-1]
                
                if has_next:
                    next_cursor = CursorInfo(
                        start_time=last_event["startTime"],
                        event_id=last_event["eventId"]
                    ).encode()
                
                if has_previous:
                    prev_cursor = CursorInfo(
                        start_time=first_event["startTime"], 
                        event_id=first_event["eventId"]
                    ).encode()
            
            return events, next_cursor, prev_cursor, has_next, has_previous
            
        except Exception as e:
            self.logger.error(f"Error in nearby events cursor pagination: {e}", exc_info=True)
            return [], None, None, False, False

    def get_external_events_paginated(self, city: str, state: str, cursor_params: CursorPaginationParams) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], bool, bool]:
        """Get cursor-paginated external events with intelligent filtering"""
        try:
            # Parse cursor
            cursor_info = None
            if cursor_params.cursor:
                cursor_info = CursorInfo.decode(cursor_params.cursor)
                if not cursor_info:
                    raise ValueError("Invalid cursor format")
            
            # Build query with location and origin filters
            query = self.collection.limit(1000000)
            query = self._apply_non_archived_filter(query)
            query = query.where("location.city", "==", city)
            query = query.where("origin", "==", "external")
            if state:
                query = query.where("location.state", "==", state)
            
            # Apply cursor-based filtering and sorting
            query = self._apply_cursor_filters(query, cursor_info, cursor_params.direction)
            query = self._apply_cursor_sorting(query)
            
            # Fetch and process events
            fetch_limit = cursor_params.page_size + 1
            if cursor_info:
                fetch_limit = min(cursor_params.page_size * 3, 100)
            
            query = query.limit(fetch_limit)
            docs = list(query.get())
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data and not event_data.get("isArchived", False):
                    event_data["eventId"] = doc.id
                    events.append(event_data)
            
            # Apply cursor filtering and pagination logic
            if cursor_info:
                events = self._filter_events_by_cursor(events, cursor_info, cursor_params.direction)
            
            if cursor_params.direction == "prev":
                has_more = len(events) > cursor_params.page_size
                if has_more:
                    events = events[-cursor_params.page_size:]
                has_next = cursor_params.cursor is not None
                has_previous = has_more
            else:
                has_more = len(events) > cursor_params.page_size
                if has_more:
                    events = events[:cursor_params.page_size]
                has_next = has_more
                has_previous = cursor_params.cursor is not None
            
            # Generate cursors
            next_cursor = None
            prev_cursor = None
            
            if events:
                first_event = events[0]
                last_event = events[-1]
                
                if has_next:
                    next_cursor = CursorInfo(
                        start_time=last_event["startTime"],
                        event_id=last_event["eventId"]
                    ).encode()
                
                if has_previous:
                    prev_cursor = CursorInfo(
                        start_time=first_event["startTime"], 
                        event_id=first_event["eventId"]
                    ).encode()
            
            return events, next_cursor, prev_cursor, has_next, has_previous
            
        except Exception as e:
            self.logger.error(f"Error in external events cursor pagination: {e}", exc_info=True)
            return [], None, None, False, False
