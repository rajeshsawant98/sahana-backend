from datetime import datetime, timedelta
from google.cloud.firestore_v1 import Query, CollectionReference
from ..base_repository import BaseRepository
from app.models.pagination import PaginationParams, EventFilters
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

    def get_all_events_paginated(self, pagination: PaginationParams, filters: Optional[EventFilters] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated events with optional filters"""
        try:
            # Build query with filters
            query = self.collection.limit(1000000)  # Start with collection query
            query = self._apply_non_archived_filter(query)
            query = self._apply_event_filters(query, filters)
            
            # Get total count before pagination
            total_count = self._get_total_count(query)
            
            # Apply sorting and pagination with defaults
            query = self._apply_sorting(query, "createdAt", "DESCENDING")
            query = self._apply_pagination(query, pagination)
            
            # Execute query
            docs = query.get()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data is not None:
                    # Double-check archived status in case of missing field
                    if event_data.get("isArchived") != True:
                        events.append(event_data)
            
            return events, total_count
        except Exception as e:
            self.logger.error(f"Error getting paginated events: {e}", exc_info=True)
            return [], 0

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

    def get_nearby_events_paginated(self, city: str, state: str, pagination: PaginationParams) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated events in a specific city and state (both manual and external)"""
        try:
            # Use single filter approach to avoid Firestore inequality limitations
            query = self.collection.where("location.city", "==", city)
            
            # Get all docs and filter in Python
            all_docs = list(query.stream())
            filtered_events = []
            for doc in all_docs:
                event_data = doc.to_dict()
                if (event_data is not None and 
                    event_data.get("isArchived") != True and
                    (not state or event_data.get("location", {}).get("state") == state)):
                    filtered_events.append(event_data)
            
            total_count = len(filtered_events)
            
            # Sort by start time in Python
            filtered_events.sort(key=lambda x: x.get("startTime", ""))
            
            # Apply pagination manually
            start = pagination.offset
            end = start + pagination.page_size
            paginated_events = filtered_events[start:end]
            
            print("Events found:")
            for i in paginated_events:
                print(i.get("name"))
            return paginated_events, total_count
        except Exception as e:
            self.logger.error(f"Error getting paginated nearby events: {e}", exc_info=True)
            return [], 0

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

    def get_external_events_paginated(self, city: str, state: str, pagination: PaginationParams) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated external (scraped) events in a specific city and state"""
        try:
            # Use single filter approach to avoid Firestore inequality limitations
            query = self.collection.where("location.city", "==", city)
            
            # Get all docs and filter in Python
            all_docs = list(query.stream())
            filtered_events = []
            for doc in all_docs:
                event_data = doc.to_dict()
                if (event_data is not None and 
                    event_data.get("isArchived") != True and
                    event_data.get("origin") == "external" and  # Changed from "scraped" to "external"
                    (not state or event_data.get("location", {}).get("state") == state)):
                    filtered_events.append(event_data)
            
            total_count = len(filtered_events)
            
            # Sort by start time in Python
            filtered_events.sort(key=lambda x: x.get("startTime", ""))
            
            # Apply pagination manually
            start = pagination.offset
            end = start + pagination.page_size
            paginated_events = filtered_events[start:end]
            
            return paginated_events, total_count
        except Exception as e:
            self.logger.error(f"Error getting paginated external events: {e}", exc_info=True)
            return [], 0

    def get_events_for_archiving(self) -> List[Dict[str, Any]]:
        """Get events that should be archived (ended events)"""
        try:
            # Calculate cutoff time (events that ended more than 1 day ago)
            cutoff_time = datetime.now() - timedelta(days=1)
            
            # Use single filter approach - filter by end time only
            query = self.collection.where("endTime", "<", cutoff_time)
            
            docs = query.stream()
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                if event_data is not None and event_data.get("isArchived") != True:
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
