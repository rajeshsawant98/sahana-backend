from passlib.context import CryptContext
from app.auth.firebase_init import get_firestore_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("users")

    def get_by_email(self, email: str):
        try:
            query = self.collection.where("email", "==", email).stream()
            user = next(query, None)
            return user.to_dict() if user else None
        except Exception as e:
            print(f"Error retrieving user: {str(e)}")
            return None

    def get_by_id(self, uid: str):
        try:
            doc = self.collection.document(uid).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Error retrieving user by ID: {str(e)}")
            return None

    def create_with_password(self, email: str, password: str, name: str):
        try:
            hashed_password = pwd_context.hash(password)
            self.collection.document(email).set({
                "name": name,
                "email": email,
                "password": hashed_password,
                "role": "user"
            })
            print(f"User with email {email} stored successfully")
        except Exception as e:
            print(f"Error storing user with password: {str(e)}")

    def verify_password(self, email: str, password: str):
        try:
            user_doc = self.collection.document(email).get()
            if not user_doc.exists:
                return False

            user = user_doc.to_dict()
            if not user or "password" not in user:
                return False

            return pwd_context.verify(password, user["password"])
        except Exception as e:
            print(f"Error verifying password: {str(e)}")
            return False

    def store_google_user(self, user_data: dict):
        try:
            self.collection.document(user_data["uid"]).set({
                "name": user_data["name"],
                "email": user_data["email"],
                "profile_picture": user_data["profile_picture"],
                "role": "user"
            }, merge=True)
            print(f"User data stored for: {user_data['email']}")
        except Exception as e:
            print(f"Error storing Google user: {str(e)}")

    def update_profile_by_email(self, user_data: dict, user_email: str):
        try:
            query = self.collection.where("email", "==", user_email).stream()
            user = next(query, None)

            if not user:
                print(f"No user found with email: {user_email}")
                return

            user_ref = self.collection.document(user.id)
            existing = user.to_dict() or {}

            update_fields = {
                "name": user_data.get("name", existing.get("name", "")),
                "profile_picture": user_data.get("profile_picture", existing.get("profile_picture", "")),
                "interests": user_data.get("interests", existing.get("interests", [])),
                "profession": user_data.get("profession", existing.get("profession", "")),
                "location": user_data.get("location", existing.get("location", "")),
                "bio": user_data.get("bio", existing.get("bio", "")),
                "phoneNumber": user_data.get("phoneNumber", existing.get("phoneNumber", "")),
                "birthdate": user_data.get("birthdate", existing.get("birthdate", ""))
            }

            user_ref.update(update_fields)
            print(f"User profile updated for: {user_email}")
        except Exception as e:
            print(f"Error updating user data: {str(e)}")