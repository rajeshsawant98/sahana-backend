from app.repositories.friends import FriendRepository
from app.repositories.users import UserRepository
from app.models.friend import FriendProfile
from app.utils.logger import get_service_logger, log_error_with_context, log_service_call
from typing import List, Dict, Any, Optional

class FriendManagementService:
    """Service for managing existing friendships (list friends, remove friends)"""
    
    def __init__(self, friend_repo: Optional[FriendRepository] = None, user_repo: Optional[UserRepository] = None):
        self.friend_repo = friend_repo or FriendRepository()
        self.user_repo = user_repo or UserRepository()
        self.logger = get_service_logger(__name__)

    def get_friends_list(self, user_email: str) -> List[FriendProfile]:
        """Get the list of friends for a user"""
        try:
            # Validate user exists
            user = self.user_repo.get_by_email(user_email)
            if not user:
                return []
            
            # Get friend IDs from accepted friend requests
            friend_ids = self.friend_repo.get_accepted_friendship_ids(user_email)
            
            friends = []
            for friend_id in friend_ids:
                # Get user details for each friend
                friend_user = self.user_repo.get_by_email(friend_id)
                if friend_user:
                    friend_profile = FriendProfile(
                        id=friend_user.get("email", friend_id),  # Use email as ID
                        name=friend_user.get("name", ""),
                        email=friend_user.get("email", friend_id),
                        bio=friend_user.get("bio"),
                        profile_picture=friend_user.get("profile_picture"),
                        location=friend_user.get("location"),
                        interests=friend_user.get("interests", []),
                        created_at=friend_user.get("created_at")
                    )
                    friends.append(friend_profile)
            
            return friends
            
        except Exception as e:
            context = {
                'method': 'get_friends_list',
                'user_email': user_email,
                'error_type': type(e).__name__,
                'available_methods': [method for method in dir(self.friend_repo) if not method.startswith('_')]
            }
            self.logger.error(f"Error getting friends list: {str(e)}", extra=context, exc_info=True)
            return []

    def get_friendship_status(self, current_user_email: str, user_id: str) -> Dict[str, Any]:
        """Get the friendship status between current user and another user"""
        try:
            # Validate current user exists
            current_user = self.user_repo.get_by_email(current_user_email)
            if not current_user:
                return {"success": False, "error": "Current user not found"}
            
            # Validate target user exists
            target_user = self.user_repo.get_by_email(user_id)
            if not target_user:
                return {"success": False, "error": "Target user not found"}
            
            # Get friendship status using existing repository methods
            # Check if there's an accepted request between users
            request = self.friend_repo.find_request_between_users(current_user_email, user_id, ["accepted"])
            if request:
                status = "friends"
            else:
                # Check for pending requests
                pending_request = self.friend_repo.find_request_between_users(current_user_email, user_id, ["pending"])
                if pending_request:
                    if pending_request["sender_id"] == current_user_email:
                        status = "request_sent"
                    else:
                        status = "request_received"
                else:
                    status = "none"
            
            return {
                "success": True,
                "friendship_status": status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting friendship status: {str(e)}")
            return {"success": False, "error": "Failed to get friendship status"}

    def remove_friendship(self, user_email: str, friend_email: str) -> Dict[str, Any]:
        """Remove a friendship between two users"""
        try:
            # Validate both users exist
            user = self.user_repo.get_by_email(user_email)
            friend = self.user_repo.get_by_email(friend_email)
            
            if not user or not friend:
                return {"success": False, "error": "One or both users not found"}
            
            # Get the friendship request using existing method
            request = self.friend_repo.find_request_between_users(user_email, friend_email, ["accepted"])
            if not request:
                return {"success": False, "error": "No active friendship found"}
            
            # Delete the friendship
            success = self.friend_repo.delete_friend_request(request["id"])
            
            if success:
                return {
                    "success": True,
                    "message": "Friendship removed successfully"
                }
            else:
                return {"success": False, "error": "Failed to remove friendship"}
                
        except Exception as e:
            self.logger.error(f"Error removing friendship: {str(e)}")
            return {"success": False, "error": "Failed to remove friendship"}

# Create service instance
friend_management_service = FriendManagementService()
