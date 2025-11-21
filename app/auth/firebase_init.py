from dotenv import load_dotenv
import os
import firebase_admin
from app import config
from firebase_admin import credentials, firestore

# Load environment variables from .env
load_dotenv()

# Get the credential path from the environment
firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize Firebase App (only once)
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(config.firebase_cred_path)
        firebase_admin.initialize_app(cred)

# Return Firestore client
def get_firestore_client():
    initialize_firebase()
    return firestore.AsyncClient()