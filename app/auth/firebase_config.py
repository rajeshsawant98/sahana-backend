from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get the credential path from the environment
firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
def initialize_firebase():
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)

# Store user data in Firestore
def store_user_data(user_data):
    # Initialize Firebase if not already done
    if not firebase_admin._apps:
        initialize_firebase()

    db = firestore.client()
    user_ref = db.collection("users").document(user_data["uid"])
    user_ref.set({
        "name": user_data["name"],
        "email": user_data["email"],
        "profile_picture": user_data["profile_picture"]
    })