import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app
cred = credentials.Certificate('firebase_cred.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Reference to the 'events' collection
events_ref = db.collection('events')
docs = events_ref.stream()


from google.cloud.firestore_v1 import DocumentSnapshot
import datetime

def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return obj

events = []
for doc in docs:
    event_data = doc.to_dict()
    event_data['id'] = doc.id  # Optionally include document ID
    event_data = make_json_serializable(event_data)
    events.append(event_data)

# Save to a JSON file
with open('events_collection.json', 'w') as f:
    json.dump(events, f, indent=2)

print(f"Extracted {len(events)} events to events_collection.json")