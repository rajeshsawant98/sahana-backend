from app.auth.firebase_init import get_firestore_client

class EventIngestionRepository:
    def __init__(self, collection_name: str = "events"):
        self.db = get_firestore_client()
        self.collection = self.db.collection(collection_name)

    def save_event(self, event: dict) -> bool:
        try:
            event_id = event["eventId"]
            self.collection.document(event_id).set(event, merge=True)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save event {event.get('eventName', '?')}: {e}")
            return False

    def save_bulk_events(self, events: list[dict]) -> int:
        saved = 0
        for event in events:
            if self.save_event(event):
                saved += 1
        return saved

    def get_by_original_id(self, original_id: str) -> dict | None:
        try:
            query = self.collection.where("originalId", "==", original_id).limit(1).stream()
            result = next(query, None)
            return result.to_dict() if result else None
        except Exception as e:
            print(f"[ERROR] Lookup by originalId failed: {e}")
            return None