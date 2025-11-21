from app.auth.firebase_init import get_firestore_client
from app.utils.logger import get_service_logger
from google.cloud.firestore import FieldFilter, Query
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

class FriendRepository:
    """
    Repository for friend request data access.
    Contains ONLY data access logic - no business rules.
    """
    
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("friend_requests")
        self.logger = get_service_logger(__name__)

    # ==================== BASIC CRUD OPERATIONS ====================
    
    async def create_friend_request(self, sender_id: str, receiver_id: str) -> str:
        """Create a new friend request record"""
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
            
            await self.collection.document(request_id).set(request_data)
            return request_id
        except Exception as e:
            self.logger.error(f"Error creating friend request: {str(e)}")
            raise e

    async def get_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a friend request by its ID"""
        try:
            doc = await self.collection.document(request_id).get()
            if doc.exists:
                request_data = doc.to_dict()
                if request_data:
                    request_data["id"] = doc.id
                    return request_data
            return None
        except Exception as e:
            self.logger.error(f"Error getting request by ID: {str(e)}")
            return None

    async def update_friend_request_status(self, request_id: str, status: str) -> bool:
        """Update the status of a friend request"""
        try:
            await self.collection.document(request_id).update({
                "status": status,
                "updated_at": datetime.utcnow()
            })
            return True
        except Exception as e:
            self.logger.error(f"Error updating friend request status: {str(e)}")
            return False

    async def delete_friend_request(self, request_id: str) -> bool:
        """Delete a friend request by ID"""
        try:
            await self.collection.document(request_id).delete()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting friend request: {str(e)}")
            return False

    # ==================== SIMPLE QUERY OPERATIONS ====================

    async def find_request_between_users(self, user1_id: str, user2_id: str, statuses: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Find any request between two users (either direction)"""
        try:
            if statuses is None:
                statuses = ["pending", "accepted"]
            
            # Check user1 -> user2
            query1 = self.collection.where(
                filter=FieldFilter("sender_id", "==", user1_id)
            ).where(
                filter=FieldFilter("receiver_id", "==", user2_id)
            ).where(
                filter=FieldFilter("status", "in", statuses)
            ).limit(1)
            
            docs1 = await query1.get()
            for doc in docs1:
                return {**doc.to_dict(), "id": doc.id}
            
            # Check user2 -> user1
            query2 = self.collection.where(
                filter=FieldFilter("sender_id", "==", user2_id)
            ).where(
                filter=FieldFilter("receiver_id", "==", user1_id)
            ).where(
                filter=FieldFilter("status", "in", statuses)
            ).limit(1)
            
            docs2 = await query2.get()
            for doc in docs2:
                return {**doc.to_dict(), "id": doc.id}
                
            return None
        except Exception as e:
            self.logger.error(f"Error finding request between users: {str(e)}")
            return None

    async def get_requests_for_user(self, user_id: str, direction: str = "all", status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get friend requests for a user
        
        Args:
            user_id: The user ID
            direction: 'sent', 'received', or 'all'
            status: Filter by status (optional)
        """
        try:
            requests = []
            
            # Get received requests
            if direction in ["received", "all"]:
                received_query = self.collection.where(
                    filter=FieldFilter("receiver_id", "==", user_id)
                )
                if status:
                    received_query = received_query.where(
                        filter=FieldFilter("status", "==", status)
                    )
                
                async for doc in received_query.stream():
                    request_data = doc.to_dict()
                    request_data["id"] = doc.id
                    request_data["direction"] = "received"
                    requests.append(request_data)
            
            # Get sent requests
            if direction in ["sent", "all"]:
                sent_query = self.collection.where(
                    filter=FieldFilter("sender_id", "==", user_id)
                )
                if status:
                    sent_query = sent_query.where(
                        filter=FieldFilter("status", "==", status)
                    )
                
                async for doc in sent_query.stream():
                    request_data = doc.to_dict()
                    request_data["id"] = doc.id
                    request_data["direction"] = "sent"
                    requests.append(request_data)
                    
            return requests
        except Exception as e:
            self.logger.error(f"Error getting requests for user: {str(e)}")
            return []

    async def get_accepted_friendship_ids(self, user_id: str) -> List[str]:
        """Get IDs of all users who are friends with the given user"""
        try:
            friend_ids = []
            
            # Get requests where user is sender and status is accepted
            sent_query = self.collection.where(
                filter=FieldFilter("sender_id", "==", user_id)
            ).where(
                filter=FieldFilter("status", "==", "accepted")
            )
            
            async for doc in sent_query.stream():
                request_data = doc.to_dict()
                friend_ids.append(request_data["receiver_id"])
            
            # Get requests where user is receiver and status is accepted
            received_query = self.collection.where(
                filter=FieldFilter("receiver_id", "==", user_id)
            ).where(
                filter=FieldFilter("status", "==", "accepted")
            )
            
            async for doc in received_query.stream():
                request_data = doc.to_dict()
                friend_ids.append(request_data["sender_id"])
                    
            return friend_ids
        except Exception as e:
            self.logger.error(f"Error getting friend IDs: {str(e)}")
            return []

    async def get_request_by_sender_receiver(self, sender_id: str, receiver_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific request by sender and receiver"""
        try:
            query = self.collection.where(
                filter=FieldFilter("sender_id", "==", sender_id)
            ).where(
                filter=FieldFilter("receiver_id", "==", receiver_id)
            ).limit(1)
            
            docs = await query.get()
            for doc in docs:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                return request_data
                
            return None
        except Exception as e:
            self.logger.error(f"Error getting request by sender/receiver: {str(e)}")
            return None
