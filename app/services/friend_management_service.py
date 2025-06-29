from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository
from app.models.friend import FriendProfile
from app.utils.logger import get_service_logger
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
            
            friends_data = self.friend_repo.get_friends_for_user(user_email)
            
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
            self.logger.error(f"Error getting friends list: {str(e)}")
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
            
            # Get friendship status using repository
            status = self.friend_repo.get_friendship_status(current_user_email, user_id)
            
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
            
            # Get the friendship request
            request = self.friend_repo.get_friend_request_by_users(user_email, friend_email)
            if not request or request["status"] != "accepted":
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
