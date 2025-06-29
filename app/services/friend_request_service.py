from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository
from app.models.friend import FriendRequestWithProfile, FriendProfile
from app.utils.logger import get_service_logger
from typing import List, Dict, Any, Optional

class FriendRequestService:
    """Service for managing friend requests."""
    
    def __init__(self, friend_repo: Optional[FriendRepository] = None, user_repo: Optional[UserRepository] = None):
        self.friend_repo = friend_repo or FriendRepository()
        self.user_repo = user_repo or UserRepository()
        self.logger = get_service_logger(__name__)

    def send_friend_request(self, sender_email: str, receiver_id: str) -> Dict[str, Any]:
        """Send a friend request from sender to receiver."""
        try:
            sender = self.user_repo.get_by_email(sender_email)
            if not sender:
                return {"success": False, "error": "Sender not found"}
            
            receiver = self.user_repo.get_by_email(receiver_id)
            if not receiver:
                return {"success": False, "error": "Receiver not found"}
            
            if sender_email == receiver_id:
                return {"success": False, "error": "Cannot send friend request to yourself"}
            
            existing = self.friend_repo.find_request_between_users(sender_email, receiver_id)
            if existing:
                if existing["status"] == "accepted":
                    return {"success": False, "error": "Already friends"}
                if existing["status"] == "pending":
                    return {"success": False, "error": "Friend request already pending"}
            
            request_id = self.friend_repo.create_friend_request(sender_email, receiver_id)
            return {"success": True, "message": "Friend request sent", "request_id": request_id}
            
        except Exception as e:
            self.logger.error(f"Error sending friend request: {str(e)}")
            return {"success": False, "error": "Failed to send friend request"}

    def respond_to_friend_request(self, request_id: str, accept: bool, user_email: str) -> Dict[str, Any]:
        """Accept or reject a friend request."""
        try:
            user = self.user_repo.get_by_email(user_email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            request = self.friend_repo.get_request_by_id(request_id)
            if not request:
                return {"success": False, "error": "Friend request not found"}
            
            if request["receiver_id"] != user_email:
                return {"success": False, "error": "Not authorized to respond to this request"}
            
            if request["status"] != "pending":
                return {"success": False, "error": "Friend request is no longer pending"}
            
            status = "accepted" if accept else "rejected"
            success = self.friend_repo.update_friend_request_status(request_id, status)
            
            if success:
                return {"success": True, "message": f"Friend request {status}"}
            return {"success": False, "error": "Failed to update friend request"}
                
        except Exception as e:
            self.logger.error(f"Error responding to friend request: {str(e)}")
            return {"success": False, "error": "Failed to respond to friend request"}

    def get_friend_requests(self, user_email: str) -> Dict[str, List[FriendRequestWithProfile]]:
        """Get all friend requests for a user (both sent and received)."""
        try:
            user = self.user_repo.get_by_email(user_email)
            if not user:
                return {"received": [], "sent": []}
            
            requests = self.friend_repo.get_requests_for_user(user_email, status="pending")
            received_requests = []
            sent_requests = []
            
            for request in requests:
                sender = self.user_repo.get_by_email(request["sender_id"])
                receiver = self.user_repo.get_by_email(request["receiver_id"])
                
                if not sender or not receiver:
                    continue
                
                sender_profile = self._build_friend_profile(sender, request["sender_id"])
                receiver_profile = self._build_friend_profile(receiver, request["receiver_id"])
                
                request_with_profile = FriendRequestWithProfile(
                    id=request["id"],
                    sender=sender_profile,
                    receiver=receiver_profile,
                    status=request["status"],
                    created_at=request["created_at"],
                    updated_at=request.get("updated_at")
                )
                
                if request["direction"] == "received":
                    received_requests.append(request_with_profile)
                else:
                    sent_requests.append(request_with_profile)
            
            return {"received": received_requests, "sent": sent_requests}
            
        except Exception as e:
            self.logger.error(f"Error getting friend requests: {str(e)}")
            return {"received": [], "sent": []}

    def cancel_friend_request(self, request_id: str, user_email: str) -> Dict[str, Any]:
        """Cancel a sent friend request."""
        try:
            user = self.user_repo.get_by_email(user_email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            request = self.friend_repo.get_request_by_id(request_id)
            if not request:
                return {"success": False, "error": "Friend request not found"}
            
            if request["sender_id"] != user_email:
                return {"success": False, "error": "Not authorized to cancel this request"}
            
            if request["status"] != "pending":
                return {"success": False, "error": "Can only cancel pending requests"}
            
            success = self.friend_repo.delete_friend_request(request_id)
            if success:
                return {"success": True, "message": "Friend request cancelled"}
            return {"success": False, "error": "Failed to cancel friend request"}
                
        except Exception as e:
            self.logger.error(f"Error cancelling friend request: {str(e)}")
            return {"success": False, "error": "Failed to cancel friend request"}

    def _build_friend_profile(self, user_data: Dict[str, Any], user_id: str) -> FriendProfile:
        """Build a friend profile from user data."""
        return FriendProfile(
            id=user_id,
            name=user_data.get("name", ""),
            email=user_data.get("email", ""),
            bio=user_data.get("bio"),
            profile_picture=user_data.get("profile_picture"),
            location=user_data.get("location"),
            interests=user_data.get("interests", [])
        )
