from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from google.cloud.firestore_v1 import ArrayRemove
from app.auth.firebase_config import get_firestore_client

# Load environment variables
load_dotenv()

# Firebase credentials
firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Create a new event
def create_event(event_data):
    try:
        db = get_firestore_client()
        events_ref = db.collection("events")

        # Generate unique event ID
        event_doc = events_ref.document()
        event_id = event_doc.id

        # Set common event fields
        event_payload = {
            "eventId": event_id,
            "eventName": event_data["eventName"],
            "location": event_data["location"],
            "startTime": event_data["startTime"],
            "duration": event_data["duration"],
            "categories": event_data["categories"],
            "isOnline": event_data.get("isOnline", False),
            "joinLink": event_data.get("joinLink", ""),
            "imageURL": event_data.get("imageURL", ""),
            "createdBy": event_data["createdBy"],
            "createdByEmail": event_data["createdByEmail"],
            "createdAt": datetime.utcnow().isoformat(),
            "description": event_data.get("description", "No description available"),
            "rsvpList": [],
            "origin": "community",
            "source": "user",
        }

        # Save to Firestore
        event_doc.set(event_payload)

        print(f"Event '{event_payload['eventName']}' created successfully!")
        return {"eventId": event_id}
    except Exception as e:
        print(f"Error creating event: {str(e)}")
        return None

# Retrieve all events
def get_all_events():
    try:
        db = get_firestore_client()
        events_ref = db.collection("events").stream()

        events = []
        for event in events_ref:
            events.append(event.to_dict())

        return events
    except Exception as e:
        print(f"Error fetching events: {str(e)}")
        return []

# Get event by ID
def get_event_by_id(event_id: str):
    try:
        db = get_firestore_client()

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
        db = get_firestore_client()
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

# Delete event
def delete_event(event_id):
    try:
        db = get_firestore_client()
        event_ref = db.collection("events").document(event_id)

        if event_ref.get().exists:
            event_ref.delete()
            print(f"Event '{event_id}' deleted successfully!")
            return True
        else:
            print(f"No event found with ID: {event_id}")
            return False
    except Exception as e:
        print(f"Error deleting event: {str(e)}")
        return False
    
# Fetch events created by a specific user
    
def get_my_events(email):
    try:
        db = get_firestore_client()
        events_ref = db.collection("events").where("createdByEmail", "==", email).stream()

        events = []
        for event in events_ref:
            events.append(event.to_dict())

        return events
    except Exception as e:
        print(f"Error fetching events by user: {str(e)}")
        return []

# RSVP to event
def rsvp_to_event(event_id, email):
    try:
        db = get_firestore_client()
        event_ref = db.collection("events").document(event_id)
        event = event_ref.get()

        if event.exists:
            event_dict = event.to_dict()
            if event_dict is not None:
                rsvp_list = event_dict.get("rsvpList", [])
            else:
                rsvp_list = []
            rsvp_list.append(email)
            event_ref.update({"rsvpList": rsvp_list})
            print(f"User '{email}' RSVP'd to event '{event_id}'")
            return True
        else:
            print(f"No event found with ID: {event_id}")
            return False
    except Exception as e:
        print(f"Error RSVP'ing to event: {str(e)}")
        return False

# Cancel RSVP
def cancel_user_rsvp(event_id: str, user_email: str):
    try:
        db = get_firestore_client()

        event_ref = db.collection("events").document(event_id)

        event_ref.update({
            "rsvpList": ArrayRemove([user_email])
        })

        # Optionally delete RSVP subdocument
        rsvp_doc = event_ref.collection("rsvps").document(user_email)
        rsvp_doc.delete()

        return {"message": "RSVP cancelled successfully"}
    except Exception as e:
        raise Exception(f"Error cancelling RSVP: {str(e)}")
    

# Fetch RSVP list for an event
def get_rsvp_list(event_id):
    try:
        db = get_firestore_client()
        event_ref = db.collection("events").document(event_id)
        event = event_ref.get()

        if event.exists:
            event_dict = event.to_dict()
            if event_dict is not None:
                rsvp_list = event_dict.get("rsvpList", [])
            else:
                rsvp_list = []
            return rsvp_list
        else:
            print(f"No event found with ID: {event_id}")
            return []
    except Exception as e:
        print(f"Error fetching RSVP list: {str(e)}")
        return []
    
    
#Fetch events RSVP'd by a specific user
def get_user_rsvps(email):
    try:
        db = get_firestore_client()
        events_ref = db.collection("events").where("rsvpList", "array_contains", email).stream()

        events = []
        for event in events_ref:
            events.append(event.to_dict())

        return events
    except Exception as e:
        print(f"Error fetching user RSVPs: {str(e)}")
        return []
    
def get_nearby_events(city: str, state: str) -> list[dict]:
    db = get_firestore_client()
    print(f"📥 Querying for city: {city}, state: {state}")

    ref = db.collection("events")
    query = (
        ref.where("location.city", "==", city)
           .where("location.state", "==", state)
           .order_by("startTime")
           .limit(30)
    )

    events = [doc.to_dict() for doc in query.stream()]
    print(f"📤 Found {len(events)} external events")
    return events