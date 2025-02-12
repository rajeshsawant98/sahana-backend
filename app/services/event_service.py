from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Load environment variables
load_dotenv()

# Firebase credentials
firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)

# Store event data in Firestore
def create_event(event_data):
    try:
        initialize_firebase()
        db = firestore.client()
        events_ref = db.collection("events")
        
        # Generate unique event ID
        event_doc = events_ref.document()
        event_id = event_doc.id
        
        event_doc.set({
            "eventId": event_id,
            "eventName": event_data["eventName"],
            "location": event_data["location"],
            "startTime": event_data["startTime"],  # ISO format string
            "duration": event_data["duration"],  # In minutes
            "categories": event_data["categories"],  # List of categories
            "isOnline": event_data["isOnline"],
            "joinLink": event_data.get("joinLink", ""),
            "imageURL": event_data.get("imageURL", ""),
            "createdBy": event_data["createdBy"],  # User who created the event
            "createdByEmail": event_data["createdByEmail"],
            "createdAt": datetime.utcnow().isoformat()
        })

        print(f"Event '{event_data['eventName']}' created successfully!")
        return {"eventId": event_id}
    except Exception as e:
        print(f"Error creating event: {str(e)}")
        return None

# Retrieve all events
def get_all_events():
    try:
        initialize_firebase()
        db = firestore.client()
        events_ref = db.collection("events").stream()

        events = []
        for event in events_ref:
            events.append(event.to_dict())

        return events
    except Exception as e:
        print(f"Error fetching events: {str(e)}")
        return []

# Get event by ID
def get_event_by_id(event_id):
    try:
        initialize_firebase()
        db = firestore.client()
        event_ref = db.collection("events").document(event_id)
        event = event_ref.get()

        if event.exists:
            return event.to_dict()
        return None
    except Exception as e:
        print(f"Error fetching event by ID: {str(e)}")
        return None

# Update event details
def update_event(event_id, update_data):
    try:
        initialize_firebase()
        db = firestore.client()
        event_ref = db.collection("events").document(event_id)

        if event_ref.get().exists:
            event_ref.update(update_data)
            print(f"Event '{event_id}' updated successfully!")
            return True
        else:
            print(f"No event found with ID: {event_id}")
            return False
    except Exception as e:
        print(f"Error updating event: {str(e)}")
        return False
    
def get_my_events(email):
    try:
        initialize_firebase()
        db = firestore.client()
        events_ref = db.collection("events").where("createdByEmail", "==", email).stream()

        events = []
        for event in events_ref:
            events.append(event.to_dict())

        return events
    except Exception as e:
        print(f"Error fetching events by user: {str(e)}")
        return []