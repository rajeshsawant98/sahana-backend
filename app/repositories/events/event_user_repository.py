from ..base_repository import BaseRepository
from app.models.pagination import PaginationParams
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Dict, Any

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

    def get_events_by_creator_paginated(self, email: str, pagination: PaginationParams) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated events created by a specific user"""
        try:
            # Build query - start with user filter first to avoid multiple != issues
            query = self.collection.where("createdByEmail", "==", email)
            
            # Get total count - filter out archived events in code
            all_docs = list(query.stream())
            non_archived_events = []
            for doc in all_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    non_archived_events.append(event_data)
            
            total_count = len(non_archived_events)
            
            # Apply sorting
            non_archived_events.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            
            # Apply pagination manually
            start = pagination.offset
            end = start + pagination.page_size
            paginated_events = non_archived_events[start:end]
            
            return paginated_events, total_count
        except Exception as e:
            self.logger.error(f"Error getting paginated events by creator {email}: {e}", exc_info=True)
            return [], 0

    def get_events_organized_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all events organized by a specific user"""
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
            self.logger.error(f"Error getting events organized by {user_email}: {e}", exc_info=True)
            return []

    def get_events_organized_by_user_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated events organized by a specific user"""
        try:
            # Build query
            query = self.collection.where("organizers", "array_contains", user_email)
            
            # Get all docs and filter archived events
            all_docs = list(query.stream())
            non_archived_events = []
            for doc in all_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    non_archived_events.append(event_data)
            
            total_count = len(non_archived_events)
            
            # Apply sorting
            non_archived_events.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            
            # Apply pagination manually
            start = pagination.offset
            end = start + pagination.page_size
            paginated_events = non_archived_events[start:end]
                    
            return paginated_events, total_count
        except Exception as e:
            self.logger.error(f"Error getting paginated events organized by {user_email}: {e}", exc_info=True)
            return [], 0

    def get_events_moderated_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Get all events moderated by a specific user"""
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
            self.logger.error(f"Error getting events moderated by {user_email}: {e}", exc_info=True)
            return []

    def get_events_moderated_by_user_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated events moderated by a specific user"""
        try:
            # Build query
            query = self.collection.where("moderators", "array_contains", user_email)
            
            # Get all docs and filter archived events
            all_docs = list(query.stream())
            non_archived_events = []
            for doc in all_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    non_archived_events.append(event_data)
            
            total_count = len(non_archived_events)
            
            # Apply sorting
            non_archived_events.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            
            # Apply pagination manually
            start = pagination.offset
            end = start + pagination.page_size
            paginated_events = non_archived_events[start:end]
                    
            return paginated_events, total_count
        except Exception as e:
            self.logger.error(f"Error getting paginated events moderated by {user_email}: {e}", exc_info=True)
            return [], 0

    def update_event_roles(self, event_id: str, field: str, emails: List[str]) -> bool:
        """Update event roles (organizers or moderators)"""
        try:
            if field not in ["organizers", "moderators"]:
                self.logger.error(f"Invalid field for event roles: {field}")
                return False
                
            event_ref = self.collection.document(event_id)
            event_ref.update({field: emails})
            
            self.logger.info(f"Updated {field} for event {event_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating event roles for {event_id}: {e}", exc_info=True)
            return False

    def get_user_event_summary(self, user_email: str) -> Dict[str, Any]:
        """Get a summary of all events related to a user"""
        try:
            summary = {
                "created_count": 0,
                "organized_count": 0,
                "moderated_count": 0,
                "rsvp_count": 0
            }
            
            # Count created events - filter out archived in Python
            created_query = self.collection.where("createdByEmail", "==", user_email)
            created_docs = list(created_query.stream())
            created_count = 0
            for doc in created_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    created_count += 1
            summary["created_count"] = created_count
            
            # Count organized events - filter out archived in Python
            organized_query = self.collection.where("organizers", "array_contains", user_email)
            organized_docs = list(organized_query.stream())
            organized_count = 0
            for doc in organized_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    organized_count += 1
            summary["organized_count"] = organized_count
            
            # Count moderated events - filter out archived in Python
            moderated_query = self.collection.where("moderators", "array_contains", user_email)
            moderated_docs = list(moderated_query.stream())
            moderated_count = 0
            for doc in moderated_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    moderated_count += 1
            summary["moderated_count"] = moderated_count
            
            # Count RSVP events - filter out archived in Python
            rsvp_query = self.collection.where("rsvpList", "array_contains", user_email)
            rsvp_docs = list(rsvp_query.stream())
            rsvp_count = 0
            for doc in rsvp_docs:
                event_data = doc.to_dict()
                if event_data and event_data.get("isArchived") != True:
                    rsvp_count += 1
            summary["rsvp_count"] = rsvp_count
            
            return summary
        except Exception as e:
            self.logger.error(f"Error getting user event summary for {user_email}: {e}", exc_info=True)
            return {"created_count": 0, "organized_count": 0, "moderated_count": 0, "rsvp_count": 0}
