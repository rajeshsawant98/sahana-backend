from datetime import datetime
from google.cloud.firestore_v1 import ArrayRemove
from app.auth.firebase_init import get_firestore_client
from app.models.pagination import PaginationParams, EventFilters
from typing import Tuple, List, Optional

class EventRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("events")

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
            "source": "user"
        }
        doc.set(event_payload)
        return {"eventId": event_id}

    def get_event_by_id(self, event_id: str) -> dict | None:
        doc = self.collection.document(event_id).get()
        return doc.to_dict() if doc.exists else None

    def get_all_events(self) -> list[dict]:
        return [doc.to_dict() for doc in self.collection.stream()]

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

    def get_events_by_creator(self, email: str) -> list[dict]:
        query = self.collection.where("createdByEmail", "==", email).stream()
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
        query = self.collection.where("rsvpList", "array_contains", user_email).stream()
        return [doc.to_dict() for doc in query]
    
    def get_events_organized_by_user(self, user_email: str) -> list[dict]:
        query = self.collection.where("organizers", "array_contains", user_email).stream()
        return [doc.to_dict() for doc in query]
    
    def get_events_moderated_by_user(self, user_email: str) -> list[dict]:
        query = self.collection.where("moderators", "array_contains", user_email).stream()
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
        query = self.collection
        
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
        query = self.collection.where("createdByEmail", "==", email).order_by("createdAt", direction="DESCENDING")
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_user_rsvps_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events that user has RSVP'd to"""
        query = self.collection.where("rsvpList", "array_contains", user_email).order_by("startTime")
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_events_organized_by_user_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events organized by a specific user"""
        query = self.collection.where("organizers", "array_contains", user_email).order_by("createdAt", direction="DESCENDING")
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        return events, total_count

    def get_events_moderated_by_user_paginated(self, user_email: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get paginated events moderated by a specific user"""
        query = self.collection.where("moderators", "array_contains", user_email).order_by("createdAt", direction="DESCENDING")
        
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
            .order_by("startTime")
        )
        
        # Get total count
        total_count = len(list(query.stream()))
        
        # Apply pagination
        query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
        events = [doc.to_dict() for doc in query_paginated.stream()]
        
        print(f"📤 Found {len(events)} external events (page {pagination.page})")
        return events, total_count