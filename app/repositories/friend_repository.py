from app.auth.firebase_init import get_firestore_client
from app.repositories.user_repository import UserRepository
from app.utils.logger import get_service_logger
from google.cloud.firestore import FieldFilter, Query
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

class FriendRepository:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("friend_requests")
        self.users_collection = self.db.collection("users")
        self.user_repo = UserRepository()
        self.logger = get_service_logger(__name__)

    def create_friend_request(self, sender_id: str, receiver_id: str) -> str:
        """Create a new friend request"""
        try:
            request_id = str(uuid.uuid4())
            request_data = {
                "id": request_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            self.collection.document(request_id).set(request_data)
            return request_id
        except Exception as e:
            self.logger.error(f"Error creating friend request: {str(e)}")
            raise e

    def get_friend_request_by_users(self, sender_id: str, receiver_id: str) -> Optional[Dict[str, Any]]:
        """Check if a friend request exists between two users (in either direction)"""
        try:
            # Check sender -> receiver
            query1 = self.collection.where(
                filter=FieldFilter("sender_id", "==", sender_id)
            ).where(
                filter=FieldFilter("receiver_id", "==", receiver_id)
            ).where(
                filter=FieldFilter("status", "in", ["pending", "accepted"])
            ).limit(1).stream()
            
            for doc in query1:
                return {**doc.to_dict(), "id": doc.id}
            
            # Check receiver -> sender
            query2 = self.collection.where(
                filter=FieldFilter("sender_id", "==", receiver_id)
            ).where(
                filter=FieldFilter("receiver_id", "==", sender_id)
            ).where(
                filter=FieldFilter("status", "in", ["pending", "accepted"])
            ).limit(1).stream()
            
            for doc in query2:
                return {**doc.to_dict(), "id": doc.id}
                
            return None
        except Exception as e:
            self.logger.error(f"Error checking friend request: {str(e)}")
            return None

    def get_pending_requests_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all pending friend requests for a user (both sent and received)"""
        try:
            requests = []
            
            # Get received requests
            received_query = self.collection.where(
                filter=FieldFilter("receiver_id", "==", user_id)
            ).where(
                filter=FieldFilter("status", "==", "pending")
            ).stream()
            
            for doc in received_query:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                request_data["direction"] = "received"
                requests.append(request_data)
            
            # Get sent requests
            sent_query = self.collection.where(
                filter=FieldFilter("sender_id", "==", user_id)
            ).where(
                filter=FieldFilter("status", "==", "pending")
            ).stream()
            
            for doc in sent_query:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                request_data["direction"] = "sent"
                requests.append(request_data)
                
            return requests
        except Exception as e:
            self.logger.error(f"Error getting pending requests: {str(e)}")
            return []

    def update_friend_request_status(self, request_id: str, status: str) -> bool:
        """Update the status of a friend request"""
        try:
            self.collection.document(request_id).update({
                "status": status,
                "updated_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            self.logger.error(f"Error updating friend request status: {str(e)}")
            return False

    def delete_friend_request(self, request_id: str) -> bool:
        """Delete a friend request"""
        try:
            self.collection.document(request_id).delete()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting friend request: {str(e)}")
            return False

    def get_friends_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accepted friends for a user"""
        try:
            friends = []
            
            # Get requests where user is sender and status is accepted
            sent_query = self.collection.where(
                filter=FieldFilter("sender_id", "==", user_id)
            ).where(
                filter=FieldFilter("status", "==", "accepted")
            ).stream()
            
            for doc in sent_query:
                request_data = doc.to_dict()
                friend_id = request_data["receiver_id"]
                friend_data = self.user_repo.get_by_id(friend_id)
                if friend_data:
                    friends.append(friend_data)
            
            # Get requests where user is receiver and status is accepted
            received_query = self.collection.where(
                filter=FieldFilter("receiver_id", "==", user_id)
            ).where(
                filter=FieldFilter("status", "==", "accepted")
            ).stream()
            
            for doc in received_query:
                request_data = doc.to_dict()
                friend_id = request_data["sender_id"]
                friend_data = self.user_repo.get_by_id(friend_id)
                if friend_data:
                    friends.append(friend_data)
                    
            return friends
        except Exception as e:
            self.logger.error(f"Error getting friends: {str(e)}")
            return []

    def search_users(self, search_term: str, current_user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for users by name or email (excluding current user)"""
        try:
            users = []
            
            # Search by name (case-insensitive contains)
            name_query = self.users_collection.order_by("name").start_at([search_term.lower()]).end_at([search_term.lower() + "\uf8ff"]).limit(limit).stream()
            
            for doc in name_query:
                user_data = doc.to_dict()
                if user_data and doc.id != current_user_id:  # Exclude current user
                    user_data["id"] = doc.id
                    users.append(user_data)
            
            # Search by email if not many results from name search
            if len(users) < limit:
                email_query = self.users_collection.where(
                    filter=FieldFilter("email", ">=", search_term.lower())
                ).where(
                    filter=FieldFilter("email", "<=", search_term.lower() + "\uf8ff")
                ).limit(limit - len(users)).stream()
                
                for doc in email_query:
                    user_data = doc.to_dict()
                    if user_data and doc.id != current_user_id and user_data not in users:  # Exclude current user and duplicates
                        user_data["id"] = doc.id
                        users.append(user_data)
                        
            return users[:limit]
        except Exception as e:
            self.logger.error(f"Error searching users: {str(e)}")
            return []

    def get_friendship_status(self, user_id: str, other_user_id: str) -> str:
        """Get the friendship status between two users"""
        try:
            request = self.get_friend_request_by_users(user_id, other_user_id)
            if not request:
                return "none"
                
            if request["status"] == "accepted":
                return "friends"
            elif request["status"] == "pending":
                if request["sender_id"] == user_id:
                    return "pending_sent"
                else:
                    return "pending_received"
            
            return "none"
        except Exception as e:
            self.logger.error(f"Error getting friendship status: {str(e)}")
            return "none"

    def get_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a friend request by its ID"""
        try:
            doc = self.collection.document(request_id).get()
            if doc.exists:
                request_data = doc.to_dict()
                if request_data:
                    request_data["id"] = doc.id
                    return request_data
            return None
        except Exception as e:
            self.logger.error(f"Error getting request by ID: {str(e)}")
            return None
