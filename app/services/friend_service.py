from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository
from app.models.friend import FriendRequestWithProfile, FriendProfile, UserSearchResult
from app.utils.logger import get_service_logger
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

friend_repo = FriendRepository()
user_repo = UserRepository()
logger = get_service_logger(__name__)

class FriendService:
    
    @staticmethod
    def send_friend_request(sender_email: str, receiver_id: str) -> Dict[str, Any]:
        """Send a friend request from sender to receiver"""
        try:
            # Validate sender exists
            sender = user_repo.get_by_email(sender_email)
            if not sender:
                return {"success": False, "error": "Sender not found"}
            
            # Since all users now use email as document ID, receiver_id should be an email
            receiver = user_repo.get_by_email(receiver_id)
            if not receiver:
                return {"success": False, "error": "Receiver not found"}
            
            # Check if sender and receiver are the same
            if sender_email == receiver_id:
                return {"success": False, "error": "Cannot send friend request to yourself"}
            
            # Check if there's already a request or friendship
            existing_request = friend_repo.get_friend_request_by_users(sender_email, receiver_id)
            if existing_request:
                if existing_request["status"] == "accepted":
                    return {"success": False, "error": "Already friends"}
                elif existing_request["status"] == "pending":
                    return {"success": False, "error": "Friend request already pending"}
            
            # Create the friend request
            request_id = friend_repo.create_friend_request(sender_email, receiver_id)
            
            return {
                "success": True, 
                "message": "Friend request sent successfully",
                "request_id": request_id
            }
            
        except Exception as e:
            logger.error(f"Error sending friend request: {str(e)}")
            return {"success": False, "error": "Failed to send friend request"}

    @staticmethod
    def get_friend_requests(user_email: str) -> Dict[str, List[FriendRequestWithProfile]]:
        """Get all friend requests for a user (both sent and received)"""
        try:
            # Get pending requests for the user - now simplified since all users use email as ID
            user = user_repo.get_by_email(user_email)
            if not user:
                return {"received": [], "sent": []}
            
            requests = friend_repo.get_pending_requests_for_user(user_email)
            
            received_requests = []
            sent_requests = []
            
            for request in requests:
                # Get sender and receiver profiles - both using email lookups
                sender = user_repo.get_by_email(request["sender_id"])
                receiver = user_repo.get_by_email(request["receiver_id"])
                
                if not sender or not receiver:
                    continue
                    
                sender_profile = FriendProfile(
                    id=request["sender_id"],
                    name=sender.get("name", ""),
                    email=sender.get("email", ""),
                    bio=sender.get("bio"),
                    profile_picture=sender.get("profile_picture"),
                    location=sender.get("location"),
                    interests=sender.get("interests", [])
                )
                
                receiver_profile = FriendProfile(
                    id=request["receiver_id"],
                    name=receiver.get("name", ""),
                    email=receiver.get("email", ""),
                    bio=receiver.get("bio"),
                    profile_picture=receiver.get("profile_picture"),
                    location=receiver.get("location"),
                    interests=receiver.get("interests", [])
                )
                
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
            
            return {
                "received": received_requests,
                "sent": sent_requests
            }
            
        except Exception as e:
            logger.error(f"Error getting friend requests: {str(e)}")
            return {"received": [], "sent": []}

    @staticmethod
    def respond_to_friend_request(request_id: str, accept: bool, user_email: str) -> Dict[str, Any]:
        """Accept or reject a friend request"""
        try:
            # Simplified - user_email is the document ID
            user = user_repo.get_by_email(user_email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get the request
            request = friend_repo.get_request_by_id(request_id)
            if not request:
                return {"success": False, "error": "Friend request not found"}
            
            # Verify the current user is the receiver
            if request["receiver_id"] != user_email:
                return {"success": False, "error": "Not authorized to respond to this request"}
            
            # Check if request is still pending
            if request["status"] != "pending":
                return {"success": False, "error": "Friend request is no longer pending"}
            
            # Update the request status
            new_status = "accepted" if accept else "rejected"
            success = friend_repo.update_friend_request_status(request_id, new_status)
            
            if success:
                action = "accepted" if accept else "rejected"
                return {
                    "success": True,
                    "message": f"Friend request {action} successfully"
                }
            else:
                return {"success": False, "error": "Failed to update friend request"}
                
        except Exception as e:
            logger.error(f"Error responding to friend request: {str(e)}")
            return {"success": False, "error": "Failed to respond to friend request"}

    @staticmethod
    def cancel_friend_request(request_id: str, user_email: str) -> Dict[str, Any]:
        """Cancel a sent friend request"""
        try:
            # Simplified - user_email is the document ID
            user = user_repo.get_by_email(user_email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get the request
            request = friend_repo.get_request_by_id(request_id)
            if not request:
                return {"success": False, "error": "Friend request not found"}
            
            # Verify the current user is the sender
            if request["sender_id"] != user_email:
                return {"success": False, "error": "Not authorized to cancel this request"}
            
            # Check if request is still pending
            if request["status"] != "pending":
                return {"success": False, "error": "Can only cancel pending friend requests"}
            
            # Delete the request
            success = friend_repo.delete_friend_request(request_id)
            
            if success:
                return {
                    "success": True,
                    "message": "Friend request cancelled successfully"
                }
            else:
                return {"success": False, "error": "Failed to cancel friend request"}
                
        except Exception as e:
            logger.error(f"Error cancelling friend request: {str(e)}")
            return {"success": False, "error": "Failed to cancel friend request"}

    @staticmethod
    def get_friends_list(user_email: str) -> List[FriendProfile]:
        """Get the list of friends for a user"""
        try:
            # Simplified - user_email is the document ID
            user = user_repo.get_by_email(user_email)
            if not user:
                return []
            
            friends_data = friend_repo.get_friends_for_user(user_email)
            
            friends = []
            for friend_data in friends_data:
                friend_profile = FriendProfile(
                    id=friend_data["id"],
                    name=friend_data.get("name", ""),
                    email=friend_data.get("email", ""),
                    bio=friend_data.get("bio"),
                    profile_picture=friend_data.get("profile_picture"),
                    location=friend_data.get("location"),
                    interests=friend_data.get("interests", []),
                    created_at=friend_data.get("created_at")
                )
                friends.append(friend_profile)
            
            return friends
            
        except Exception as e:
            logger.error(f"Error getting friends list: {str(e)}")
            return []

    @staticmethod
    def search_users(search_term: str, user_email: str, limit: int = 20) -> List[UserSearchResult]:
        """Search for users and include friendship status"""
        try:
            # Simplified - user_email is the document ID
            current_user = user_repo.get_by_email(user_email)
            if not current_user:
                return []
            
            users_data = friend_repo.search_users(search_term, user_email, limit)
            
            search_results = []
            for user_data in users_data:
                # Get friendship status
                friendship_status = friend_repo.get_friendship_status(user_email, user_data["id"])
                
                # Ensure friendship_status is one of the valid literal values
                valid_status: Literal["friends", "pending_sent", "pending_received", "none"] = "none"
                if friendship_status in ["friends", "pending_sent", "pending_received", "none"]:
                    valid_status = friendship_status  # type: ignore
                
                user_result = UserSearchResult(
                    id=user_data["id"],
                    name=user_data.get("name", ""),
                    email=user_data.get("email", ""),
                    bio=user_data.get("bio"),
                    profile_picture=user_data.get("profile_picture"),
                    location=user_data.get("location"),
                    interests=user_data.get("interests", []),
                    friendship_status=valid_status
                )
                search_results.append(user_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []

# Create service instance
friend_service = FriendService()
