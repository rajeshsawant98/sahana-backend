from dotenv import load_dotenv
import os
from passlib.context import CryptContext  # Passlib context for hashing
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables from .env
load_dotenv()

# Get the credential path from the environment
firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize password hashing context using bcrypt (same as in routes)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)

# Store user data in Firestore (Google Login or Normal Login)
def store_user_data(user_data):
    try:
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
        print(f"User data stored for: {user_data['email']}")
    except Exception as e:
        print(f"Error storing user data: {str(e)}")

# Store user with password (for normal login)
def store_user_with_password(email, password, name):
    try:
        if not firebase_admin._apps:
            initialize_firebase()

        db = firestore.client()
        user_ref = db.collection("users").document(email)

        # Hash the password before storing it using Passlib
        hashed_password = pwd_context.hash(password)

        user_ref.set({
            "name": name,
            "email": email,
            "password": hashed_password
        })
        print(f"User with email {email} stored successfully")
    except Exception as e:
        print(f"Error storing user with password: {str(e)}")

# Verify user password (for normal login)
def verify_user_password(email, password):
    try:
        if not firebase_admin._apps:
            initialize_firebase()

        db = firestore.client()
        user_ref = db.collection("users").document(email)
        user = user_ref.get()

        if not user.exists:
            print(f"No user found with email: {email}")
            return False

        user_data = user.to_dict()

        # Ensure the password field exists
        if "password" not in user_data:
            print(f"Password missing for user: {email}")
            return False

        # Verify the password using Passlib's context
        is_verified = pwd_context.verify(password, user_data["password"])
        if is_verified:
            print(f"Password verified for user: {email}")
        else:
            print(f"Password mismatch for user: {email}")
        return is_verified
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        return False

# Retrieve user data by email
def get_user_by_email(email: str):
    try:
        if not firebase_admin._apps:
            initialize_firebase()

        db = firestore.client()
        user_ref = db.collection("users").document(email)
        user = user_ref.get()

        if user.exists:
            return user.to_dict()
        print(f"No user found with email: {email}")
        return None
    except Exception as e:
        print(f"Error retrieving user data by email: {str(e)}")
        return None