from passlib.context import CryptContext
from app.auth.firebase_init import get_firestore_client
from app.models.pagination import PaginationParams, UserFilters
from app.utils.logger import get_service_logger
from typing import Tuple, List, Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("users")
        self.logger = get_service_logger(__name__)
    
    def get_all_users(self):
        try:
            users = self.collection.stream()
            return [user.to_dict() for user in users]
        except Exception as e:
            self.logger.error(f"Error retrieving users: {str(e)}")
            return []

    def get_all_users_paginated(self, pagination: PaginationParams, filters: Optional[UserFilters] = None) -> Tuple[List[dict], int]:
        """Get paginated users with optional filters"""
        try:
            query = self.collection
            
            # Apply filters if provided
            if filters:
                if filters.role:
                    query = query.where("role", "==", filters.role)
                if filters.profession:
                    query = query.where("profession", "==", filters.profession)
            
            # Order by email for consistent pagination
            query = query.order_by("email")
            
            # Get total count
            total_count = len(list(query.stream()))
            
            # Apply pagination
            query_paginated = query.offset(pagination.offset).limit(pagination.page_size)
            users = [user.to_dict() for user in query_paginated.stream()]
            
            return users, total_count
        except Exception as e:
            self.logger.error(f"Error retrieving paginated users: {str(e)}")
            return [], 0

    def get_by_email(self, email: str):
        try:
            query = self.collection.where("email", "==", email).stream()
            user = next(query, None)
            if user:
                user_data = user.to_dict()
                if user_data:  # Check that user_data is not None
                    user_data["id"] = user.id  # Include the document ID
                    return user_data
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving user: {str(e)}")
            return None

    def get_by_id(self, uid: str):
        try:
            doc = self.collection.document(uid).get()
            if doc.exists:
                user_data = doc.to_dict()
                if user_data:
                    user_data["id"] = doc.id  # Include the document ID
                    return user_data
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving user by ID: {str(e)}")
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
            self.logger.info(f"User with email {email} stored successfully")
        except Exception as e:
            self.logger.error(f"Error storing user with password: {str(e)}")

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
            self.logger.error(f"Error verifying password: {str(e)}")
            return False

    def store_google_user(self, user_data: dict):
        try:
            # Use email as document ID for all users (including Google users)
            self.collection.document(user_data["email"]).set({
                "name": user_data["name"],
                "email": user_data["email"],
                "profile_picture": user_data["profile_picture"],
                "google_uid": user_data.get("uid"),  # Store Google UID as a field for reference
                "role": "user"
            }, merge=True)
            self.logger.info(f"User data stored for: {user_data['email']}")
        except Exception as e:
            self.logger.error(f"Error storing Google user: {str(e)}")

    def update_profile_by_email(self, user_data: dict, user_email: str):
        try:
            query = self.collection.where("email", "==", user_email).stream()
            user = next(query, None)

            if not user:
                self.logger.warning(f"No user found with email: {user_email}")
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
            self.logger.info(f"User profile updated for: {user_email}")
        except Exception as e:
            self.logger.error(f"Error updating user data: {str(e)}")