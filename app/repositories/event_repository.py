from datetime import datetime
from google.cloud.firestore_v1 import ArrayRemove
from app.auth.firebase_init import get_firestore_client

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
            "imageURL": data.get("imageURL", ""),
            "createdBy": data["createdBy"],
            "createdByEmail": data["createdByEmail"],
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