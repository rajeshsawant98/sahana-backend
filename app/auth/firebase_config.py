from dotenv import load_dotenv
import os
from passlib.context import CryptContext  # Passlib context for hashing
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import HTTPException

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

def get_firestore_client():
    if not firebase_admin._apps:
        initialize_firebase()
    return firestore.client()


# Store user data in Firestore (Google Login or Normal Login)
def store_user_data(user_data):
    try:
        # Initialize Firebase if not already done
        db = get_firestore_client()
        user_ref = db.collection("users").document(user_data["uid"])
        user_ref.set({
            "name": user_data["name"],
            "email": user_data["email"],
            "profile_picture": user_data["profile_picture"],
            "role": "user" 
        }, merge=True)
        print(f"User data stored for: {user_data['email']}")
    except Exception as e:
        print(f"Error storing user data: {str(e)}")

# Store user with password (for normal login)
def store_user_with_password(email, password, name):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(email)

        # Hash the password before storing it using Passlib
        hashed_password = pwd_context.hash(password)

        user_ref.set({
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": "user" 
        })
        print(f"User with email {email} stored successfully")
    except Exception as e:
        print(f"Error storing user with password: {str(e)}")

# Verify user password (for normal login)
def verify_user_password(email, password):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(email)
        user = user_ref.get()

        if not user.exists:
            print(f"No user found with email: {email}")
            return False

        user_data = user.to_dict()

        # Ensure the password field exists
        if not user_data or "password" not in user_data:
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
        db = get_firestore_client()
        # Query the 'users' collection where the 'email' field matches the given email
        users_ref = db.collection("users")
        
        query = users_ref.where("email", "==", email)
    #   query = users_ref.where(field_path="email",op_string= "==",value= email)
        results = query.stream()

        # Check if there are any results from the query
        user = next(results, None)  # Get the first user from the query stream, or None if no users found
        if user:
            return user.to_dict()
        print(f"No user found with email: {email}")
        return None
    except Exception as e:
        print(f"Error retrieving user data by email: {str(e)}")
        return None

# Update user profile in Firestore
def update_user_data(user_data: dict, user_email: str):
    try:
        db = get_firestore_client()

        # Query the 'users' collection where the 'email' field matches the given email
        users_ref = db.collection("users")
        query = users_ref.where("email", "==", user_email)
#       query = users_ref.where(field_path="email", op_string="==", value=user_email)
        results = query.stream()

        # Get the first result (if any)
        user = next(results, None)

        if user:
            user_ref = db.collection("users").document(user.id)  # Get the document reference using the document ID
            # Update user profile with the new data
            user_ref.update({
                # Safely get the old user data as a dict, or use an empty dict if None
                "name": user_data.get("name", (user.to_dict() or {}).get("name", "")),  # Update name if provided, else keep the old name
                "profile_picture": user_data.get("profile_picture", (user.to_dict() or {}).get("profile_picture", "")),  # Update profile picture if provided
                "interests": user_data.get("interests", (user.to_dict() or {}).get("interests", [])),  # Update interests if provided, else keep the old interests
                "profession": user_data.get("profession", (user.to_dict() or {}).get("profession", "")),
                "location": user_data.get("location", (user.to_dict() or {}).get("location", "")),
                "bio": user_data.get("bio", (user.to_dict() or {}).get("bio", "")),
                "phoneNumber": user_data.get("phoneNumber", (user.to_dict() or {}).get("phoneNumber", "")),
                "birthdate": user_data.get("birthdate", (user.to_dict() or {}).get("birthdate", ""))
            })
            print(f"User profile updated for: {user_email}")
        else:
            print(f"No user found with email: {user_email}")

    except Exception as e:
        print(f"Error updating user data: {str(e)}")

# Store or update user data based on existence
def store_or_update_user_data(user_data):
    try:
        # Initialize Firebase if not already done
        db = get_firestore_client()
        user_email = user_data["email"]

        # Check if the user already exists
        existing_user = get_user_by_email(user_email)

        if existing_user:
            # User exists, update the profile
            update_user_data(user_data, user_email)
        else:
            store_user_data(user_data)

            print(f"New user profile created for: {user_email}")

    except Exception as e:
        print(f"Error storing or updating user data: {str(e)}")