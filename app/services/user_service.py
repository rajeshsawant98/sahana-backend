from passlib.context import CryptContext
from firebase_admin import firestore
from app.auth.firebase_config import get_firestore_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def store_user_data(user_data):
    try:
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

def store_user_with_password(email, password, name):
    try:
        db = get_firestore_client()
        hashed_password = pwd_context.hash(password)
        user_ref = db.collection("users").document(email)
        user_ref.set({
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": "user"
        })
        print(f"User with email {email} stored successfully")
    except Exception as e:
        print(f"Error storing user with password: {str(e)}")

def verify_user_password(email, password):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(email)
        user = user_ref.get()

        if not user.exists:
            print(f"No user found with email: {email}")
            return False

        user_data = user.to_dict()
        if not user_data or "password" not in user_data:
            print(f"Password missing for user: {email}")
            return False

        is_verified = pwd_context.verify(password, user_data["password"])
        print(f"Password {'verified' if is_verified else 'mismatch'} for user: {email}")
        return is_verified
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        return False

def get_user_by_email(email: str):
    try:
        db = get_firestore_client()
        query = db.collection("users").where("email", "==", email).stream()
        user = next(query, None)
        return user.to_dict() if user else None
    except Exception as e:
        print(f"Error retrieving user data by email: {str(e)}")
        return None

def update_user_data(user_data: dict, user_email: str):
    try:
        db = get_firestore_client()
        query = db.collection("users").where("email", "==", user_email).stream()
        user = next(query, None)

        if not user:
            print(f"No user found with email: {user_email}")
            return

        user_ref = db.collection("users").document(user.id)
        existing = user.to_dict() or {}

        user_ref.update({
            "name": user_data.get("name", existing.get("name", "")),
            "profile_picture": user_data.get("profile_picture", existing.get("profile_picture", "")),
            "interests": user_data.get("interests", existing.get("interests", [])),
            "profession": user_data.get("profession", existing.get("profession", "")),
            "location": user_data.get("location", existing.get("location", "")),
            "bio": user_data.get("bio", existing.get("bio", "")),
            "phoneNumber": user_data.get("phoneNumber", existing.get("phoneNumber", "")),
            "birthdate": user_data.get("birthdate", existing.get("birthdate", ""))
        })
        print(f"User profile updated for: {user_email}")
    except Exception as e:
        print(f"Error updating user data: {str(e)}")

def store_or_update_user_data(user_data):
    try:
        db = get_firestore_client()
        user_email = user_data["email"]
        existing_user = get_user_by_email(user_email)

        if existing_user:
            update_user_data(user_data, user_email)
        else:
            store_user_data(user_data)
            print(f"New user profile created for: {user_email}")
    except Exception as e:
        print(f"Error storing or updating user data: {str(e)}")