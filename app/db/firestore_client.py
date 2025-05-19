from app.auth.firebase_init import get_firestore_client

def save_event_to_firestore(event: dict, collection: str = "events"):
    try:
        db = get_firestore_client()
        event_id = event["eventId"]
        doc_ref = db.collection(collection).document(event_id)
        doc_ref.set(event, merge=True)
        # print(f"[✔] Saved event: {event['eventName']} ({event_id})")
    except Exception as e:
        print(f"[ERROR] Failed to save event {event.get('eventName', '?')}: {e}")