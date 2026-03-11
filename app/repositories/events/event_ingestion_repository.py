from app.auth.firebase_init import get_firestore_client
from app.utils.logger import get_repository_logger
from google.cloud.firestore_v1.base_query import FieldFilter

class EventIngestionRepository:
    def __init__(self, collection_name: str = "events"):
        self.db = get_firestore_client()
        self.collection = self.db.collection(collection_name)
        self.logger = get_repository_logger(__name__)

    async def save_event(self, event: dict) -> bool:
        try:
            event_id = event["eventId"]
            await self.collection.document(event_id).set(event, merge=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save event {event.get('eventName', '?')}: {e}")
            return False

    async def save_bulk_events(self, events: list[dict]) -> int:
        saved = 0
        for event in events:
            if await self.save_event(event):
                saved += 1
        return saved

    async def get_by_original_id(self, original_id: str) -> dict | None:
        try:
            query = self.collection.where(filter=FieldFilter("originalId", "==", original_id)).limit(1).stream()
            result = None
            async for doc in query:
                result = doc
                break
            return result.to_dict() if result else None
        except Exception as e:
            self.logger.error(f"Lookup by originalId failed: {e}")
            return None