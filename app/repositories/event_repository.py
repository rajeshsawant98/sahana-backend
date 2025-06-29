from datetime import datetime, timedelta
from google.cloud.firestore_v1 import ArrayRemove, FieldFilter
from app.auth.firebase_init import get_firestore_client
from app.models.pagination import PaginationParams, EventFilters
from app.utils.logger import get_repository_logger
from typing import Tuple, List, Optional

class EventRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("events")
        self.logger = get_repository_logger(__name__)

    def create_event(self, data: dict) -> dict:
        doc = self.collection.document()
        event_id = doc.id
        event_payload = {
            "eventId": event_id,
            "eventName": data["eventName"],
            "location": data["location"],
            "startTime": data["startTime"],
            "duration": data["duration"],
            "categories": data["categories"],
            "isOnline": data.get("isOnline", False),
            "joinLink": data.get("joinLink", ""),
            "imageUrl": data.get("imageUrl", ""),
            "createdBy": data["createdBy"],
            "createdByEmail": data["createdByEmail"],
            "organizers": data.get("organizers", []),
            "moderators": data.get("moderators", []),
            "createdAt": datetime.utcnow().isoformat(),
            "description": data.get("description", "No description available"),
            "rsvpList": [],
            "origin": "community",
            "source": "user",
            # Archive fields
            "isArchived": False,
            "archivedAt": None,
            "archivedBy": None,
            "archiveReason": None
        }
        doc.set(event_payload)
        return {"eventId": event_id}

    def get_event_by_id(self, event_id: str) -> dict | None:
        doc = self.collection.document(event_id).get()
        return doc.to_dict() if doc.exists else None

    def get_all_events(self) -> list[dict]:
        # Filter out archived events from regular queries
        query = self.collection.where("isArchived", "!=", True).stream()
        return [doc.to_dict() for doc in query]

    def update_event(self, event_id: str, update_data: dict) -> bool:
        doc_ref = self.collection.document(event_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.update(update_data)
        return True

    def delete_event(self, event_id: str) -> bool:
        doc_ref = self.collection.document(event_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    def archive_event(self, event_id: str, archived_by: str, reason: str = "Event archived") -> bool:
        """Soft delete/archive an event"""
        try:
            doc_ref = self.collection.document(event_id)
            if not doc_ref.get().exists:
                return False
            
            archive_data = {
                "isArchived": True,
                "archivedAt": datetime.utcnow().isoformat(),
                "archivedBy": archived_by,
                "archiveReason": reason
            }
            doc_ref.update(archive_data)
            return True
        except Exception as e:
            print(f"Error archiving event {event_id}: {e}")
            return False

    def unarchive_event(self, event_id: str) -> bool:
        """Restore an archived event"""
        try:
            doc_ref = self.collection.document(event_id)
            if not doc_ref.get().exists:
                return False
            
            unarchive_data = {
                "isArchived": False,
                "archivedAt": None,
                "archivedBy": None,
                "archiveReason": None
            }
            doc_ref.update(unarchive_data)
            return True
        except Exception as e:
            print(f"Error unarchiving event {event_id}: {e}")
            return False

    def get_archived_events(self, user_email: Optional[str] = None) -> list[dict]:
        """Get archived events, optionally filtered by creator"""
        try:
            query = self.collection.where("isArchived", "==", True)
            
            if user_email:
                query = query.where("createdByEmail", "==", user_email)
            
            return [doc.to_dict() for doc in query.stream()]
        except Exception as e:
            print(f"Error getting archived events: {e}")
            return []

    def get_archived_events_paginated(self, pagination: PaginationParams, user_email: Optional[str] = None) -> Tuple[List[dict], int]:
        """Get paginated archived events, optionally filtered by creator"""
        try:
            query = self.collection.where("isArchived", "==", True)
            
            if user_email:
                query = query.where("createdByEmail", "==", user_email)
            
            # Order by archived date (most recently archived first)
            # Now that composite index is created, this should work
            query = query.order_by("archivedAt", direction="DESCENDING")
            
            # Get total count
            total_count = len(list(query.stream()))
            
            # Apply pagination
            query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
            events = [doc.to_dict() for doc in query_paginated.stream()]
            
            return events, total_count
        except Exception as e:
            print(f"Error getting paginated archived events: {e}")
            return [], 0

    def archive_past_events(self, archived_by: str = "system") -> int:
        """Archive all past events (events that have ended)"""
        try:
            current_time = datetime.utcnow().isoformat()
            archived_count = 0
            
            # Get all non-archived events
            query = self.collection.where("isArchived", "!=", True).stream()
            
            for doc in query:
                event_data = doc.to_dict()
                start_time = event_data.get("startTime")
                duration = event_data.get("duration", 0)
                
                if start_time:
                    try:
                        # Parse start time and calculate end time
                        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                        end_dt = start_dt + timedelta(minutes=duration)
                        
                        # If event has ended, archive it
                        if end_dt < datetime.utcnow().replace(tzinfo=end_dt.tzinfo):
                            archive_data = {
                                "isArchived": True,
                                "archivedAt": current_time,
                                "archivedBy": archived_by,
                                "archiveReason": "Automatically archived - event ended"
                            }
                            self.collection.document(doc.id).update(archive_data)
                            archived_count += 1
                    except Exception as parse_error:
                        print(f"Error parsing date for event {doc.id}: {parse_error}")
                        continue
            
            return archived_count
        except Exception as e:
            print(f"Error archiving past events: {e}")
            return 0

    def get_events_by_creator(self, email: str) -> list[dict]:
        # Filter out archived events from regular queries
        query = self.collection.where("createdByEmail", "==", email).where("isArchived", "!=", True).stream()
        return [doc.to_dict() for doc in query]

    def rsvp_to_event(self, event_id: str, user_email: str) -> bool:
        doc_ref = self.collection.document(event_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        data = doc.to_dict() or {}
        rsvp_list = data.get("rsvpList", [])
        if user_email not in rsvp_list:
            rsvp_list.append(user_email)
            doc_ref.update({"rsvpList": rsvp_list})
        return True

    def cancel_rsvp(self, event_id: str, user_email: str) -> bool:
        doc_ref = self.collection.document(event_id)
        doc_ref.update({"rsvpList": ArrayRemove([user_email])})
        try:
            doc_ref.collection("rsvps").document(user_email).delete()
        except Exception:
            pass
        return True

    def get_user_rsvps(self, user_email: str) -> list[dict]:
        query = self.collection.where("rsvpList", "array_contains", user_email).where("isArchived", "!=", True).stream()
        return [doc.to_dict() for doc in query]
    
    def get_events_organized_by_user(self, user_email: str) -> list[dict]:
        query = self.collection.where("organizers", "array_contains", user_email).where("isArchived", "!=", True).stream()
        return [doc.to_dict() for doc in query]
    
    def get_events_moderated_by_user(self, user_email: str) -> list[dict]:
        query = self.collection.where("moderators", "array_contains", user_email).where("isArchived", "!=", True).stream()
        return [doc.to_dict() for doc in query]

    def get_rsvp_list(self, event_id: str) -> list[str]:
        doc = self.collection.document(event_id).get()
        if not doc.exists:
            return []
        doc_dict = doc.to_dict()
        if not doc_dict:
            return []
        return doc_dict.get("rsvpList", [])
    
    def get_nearby_events(self, city: str, state: str) -> list[dict]:
        query = (
            self.collection
            .where("location.city", "==", city)
            .where("location.state", "==", state)
            .where("isArchived", "!=", True)
            .order_by("startTime")
            .limit(30)
        )
        return [doc.to_dict() for doc in query.stream()]
    
    
    def get_external_events(self, city: str, state: str) -> list[dict]:
        print(f"📥 Querying external events for city: {city}, state: {state}")
        query = (
            self.collection
            .where("origin", "==", "external")
            .where("location.city", "==", city)
            .where("location.state", "==", state)
            .where("isArchived", "!=", True)
            .order_by("startTime")
            .limit(30)
        )
        events = [doc.to_dict() for doc in query.stream()]
        print(f"📤 Found {len(events)} external events")
        return events
    
    def update_event_roles(self, event_id: str, field: str, emails: list[str]) -> bool:
        try:
            event_ref = self.collection.document(event_id)
            event_ref.update({field: emails})
            return True
        except Exception as e:
            print(f"Error updating {field} for event {event_id}: {e}")
            return False
        
    def delete_events_before_today(self) -> int:
        """
        Deletes all events from the Firestore collection whose createdAt is before today.
        Returns the count of successfully deleted events.
        """
        today = datetime.utcnow().date()
        deleted_count = 0

        for doc in self.collection.stream():
            data = doc.to_dict()
            event_id = data.get("eventId")
            created_at = data.get("createdAt")

            if not event_id or not created_at:
                continue

            try:
                created_date = datetime.fromisoformat(created_at).date()
                if created_date <= today:
                    if self.delete_event(event_id):
                        print(f"🗑️ Deleted event: {event_id} ({data.get('eventName')})")
                        deleted_count += 1
            except Exception as e:
                print(f"⚠️ Failed to delete event {event_id}: {e}")

        print(f"✅ Deleted {deleted_count} old events.")
        return deleted_count
    
    def get_all_events_paginated(self, pagination: PaginationParams, filters: Optional[EventFilters] = None) -> Tuple[List[dict], int]:
        """Get paginated events with optional filters"""
        query = self.collection.where("isArchived", "!=", True)
        
        # Apply filters if provided
        if filters:
            if filters.city:
                query = query.where("location.city", "==", filters.city)
            if filters.state:
                query = query.where("location.state", "==", filters.state)
            if filters.category:
                query = query.where("categories", "array_contains", filters.category)
            if filters.is_online is not None:
                query = query.where("isOnline", "==", filters.is_online)
            if filters.creator_email:
                query = query.where("createdByEmail", "==", filters.creator_email)
            if filters.start_date:
                query = query.where("startTime", ">=", filters.start_date)
            if filters.end_date:
                query = query.where("startTime", "<=", filters.end_date)
        
        # Order by creation time (most recent first)
        query = query.order_by("createdAt", direction="DESCENDING")
        
        # Get total count for pagination metadata
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_events_by_creator_paginated(self, email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events created by a specific user"""
        try:
            # Use the new filter syntax to avoid warnings
            query = self.collection.where(
                filter=FieldFilter("createdByEmail", "==", email)
            ).where(
                filter=FieldFilter("isArchived", "!=", True)
            ).order_by("createdAt", direction="DESCENDING")
            
            # Get total count
            total_count = len(list(query.stream()))
            
            # Apply pagination
            query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
            events = [doc.to_dict() for doc in query_paginated.stream()]
            
            self.logger.debug(f"Retrieved {len(events)} events for creator {email} (page {pagination.page}, total: {total_count})")
            return events, total_count
            
        except Exception as e:
            self.logger.error(f"Error getting events by creator {email}: {str(e)}", exc_info=True)
            return [], 0

    def get_user_rsvps_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events that user has RSVP'd to"""
        try:
            # Use the new filter syntax to avoid warnings
            query = self.collection.where(
                filter=FieldFilter("rsvpList", "array_contains", user_email)
            ).where(
                filter=FieldFilter("isArchived", "!=", True)
            ).order_by("startTime")
            
            # Get total count
            total_count = len(list(query.stream()))
            
            # Apply pagination
            query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
            events = [doc.to_dict() for doc in query_paginated.stream()]
            
            self.logger.debug(f"Retrieved {len(events)} RSVP events for user {user_email} (page {pagination.page}, total: {total_count})")
            return events, total_count
            
        except Exception as e:
            self.logger.error(f"Error getting user RSVPs for {user_email}: {str(e)}", exc_info=True)
            return [], 0

    def get_events_organized_by_user_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events organized by a specific user"""
        query = self.collection.where("organizers", "array_contains", user_email).where("isArchived", "!=", True).order_by("createdAt", direction="DESCENDING")
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_events_moderated_by_user_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events moderated by a specific user"""
        query = self.collection.where("moderators", "array_contains", user_email).where("isArchived", "!=", True).order_by("createdAt", direction="DESCENDING")
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_nearby_events_paginated(self, city: str, state: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated nearby events for a specific location"""
        query = (
            self.collection
            .where("location.city", "==", city)
            .where("location.state", "==", state)
            .where("isArchived", "!=", True)
            .order_by("startTime")
        )
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_external_events_paginated(self, city: str, state: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated external events for a specific location"""
        print(f"📥 Querying external events for city: {city}, state: {state} (paginated)")
        query = (
            self.collection
            .where("origin", "==", "external")
            .where("location.city", "==", city)
            .where("location.state", "==", state)
            .where("isArchived", "!=", True)
            .order_by("startTime")
        )
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        print(f"📤 Found {len(events)} external events (page {pagination.page})")
        return events, total_count