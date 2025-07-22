import json
import logging
import os
from google.cloud import firestore
from google.oauth2 import service_account

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DATA_FILE = os.path.join(os.path.dirname(__file__), '../data/events_with_rsvp_semantic.json')
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), '../firebase_cred.json')


def main():
    # Load events from JSON
    try:
        with open(DATA_FILE, 'r') as f:
            events = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load {DATA_FILE}: {e}")
        return

    # Setup Firestore client
    try:
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        db = firestore.Client(credentials=credentials)
    except Exception as e:
        logging.error(f"Failed to initialize Firestore client: {e}")
        return

    # Process each event
    for event in events:
        event_id = event.get('id')
        rsvp_list = event.get('rsvpList')
        if not event_id or rsvp_list is None:
            logging.warning(f"Skipping event with missing id or rsvpList: {event}")
            continue

        doc_ref = db.collection('events').document(event_id)
        try:
            doc_ref.set({'rsvpList': rsvp_list}, merge=True)
            logging.info(f"Updated event {event_id} successfully.")
        except Exception as e:
            logging.error(f"Failed to update event {event_id}: {e}")

if __name__ == '__main__':
    main()
