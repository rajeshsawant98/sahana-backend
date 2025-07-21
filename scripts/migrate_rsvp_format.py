import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("firebase_cred.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def migrate_rsvps():
    events_ref = db.collection("events")
    events = events_ref.stream()
    migrated_count = 0

    for event in events:
        event_data = event.to_dict()
        rsvp_list = event_data.get("rsvpList")
        if rsvp_list and isinstance(rsvp_list, list) and rsvp_list and isinstance(rsvp_list[0], str):
            # Old format detected
            new_rsvp_list = [{"email": email, "status": "joined"} for email in rsvp_list]
            events_ref.document(event.id).update({"rsvpList": new_rsvp_list})
            migrated_count += 1
            print(f"Migrated event {event.id}: {len(rsvp_list)} RSVPs updated.")

    print(f"Migration complete. {migrated_count} events updated.")

if __name__ == "__main__":
    migrate_rsvps()