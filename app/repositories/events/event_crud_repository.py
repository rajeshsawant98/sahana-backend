from datetime import datetime
from ..base_repository import BaseRepository
from typing import Dict

class EventCrudRepository(BaseRepository):
    """Repository for basic CRUD operations on events"""
    
    def __init__(self):
        super().__init__("events")

    def create_event(self, data: dict) -> dict:
        """Create a new event"""
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
        """Get event by ID"""
        return self.get_by_id(event_id)

    def update_event(self, event_id: str, update_data: dict) -> bool:
        """Update an event"""
        return self.update_by_id(event_id, update_data)

    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        return self.delete_by_id(event_id)

    def update_event_roles(self, event_id: str, field: str, emails: list[str]) -> bool:
        """Update event roles (organizers, moderators)"""
        try:
            event_ref = self.collection.document(event_id)
            event_ref.update({field: emails})
            return True
        except Exception as e:
            self.logger.error(f"Error updating {field} for event {event_id}: {e}")
            return False
