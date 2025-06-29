from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository
from app.models.friend import UserSearchResult
from app.utils.logger import get_service_logger
from typing import List, Dict, Any, Optional, Literal

class UserDiscoveryService:
    """Service for discovering and searching users"""
    
    def __init__(self, friend_repo: Optional[FriendRepository] = None, user_repo: Optional[UserRepository] = None):
        self.friend_repo = friend_repo or FriendRepository()
        self.user_repo = user_repo or UserRepository()
        self.logger = get_service_logger(__name__)

    def search_users(self, search_term: str, user_email: str, limit: int = 20) -> List[UserSearchResult]:
        """Search for users and include friendship status"""
        try:
            # Validate current user exists
            current_user = self.user_repo.get_by_email(user_email)
            if not current_user:
                return []
            
            users_data = self.friend_repo.search_users(search_term, user_email, limit)
            
            search_results = []
            for user_data in users_data:
                # Get friendship status
                friendship_status = self.friend_repo.get_friendship_status(user_email, user_data["id"])
                
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
            self.logger.error(f"Error searching users: {str(e)}")
            return []

    def get_user_suggestions(self, user_email: str, limit: int = 10) -> List[UserSearchResult]:
        """Get friend suggestions based on mutual friends, interests, etc."""
        try:
            # Validate current user exists
            current_user = self.user_repo.get_by_email(user_email)
            if not current_user:
                return []
            
            # Get current user's interests for matching
            user_interests = current_user.get("interests", [])
            
            # For now, return users with similar interests
            # This could be enhanced with ML algorithms
            all_users = self.user_repo.get_all_users()
            suggestions = []
            
            for user_data in all_users:
                if user_data.get("email") == user_email:  # Skip current user
                    continue
                    
                # Check if already friends or has pending request
                friendship_status = self.friend_repo.get_friendship_status(user_email, user_data["id"])
                if friendship_status != "none":
                    continue
                
                # Calculate interest similarity (simple approach)
                other_interests = user_data.get("interests", [])
                common_interests = set(user_interests) & set(other_interests)
                
                if len(common_interests) > 0:  # Has common interests
                    user_result = UserSearchResult(
                        id=user_data["id"],
                        name=user_data.get("name", ""),
                        email=user_data.get("email", ""),
                        bio=user_data.get("bio"),
                        profile_picture=user_data.get("profile_picture"),
                        location=user_data.get("location"),
                        interests=user_data.get("interests", []),
                        friendship_status="none"
                    )
                    suggestions.append(user_result)
                    
                    if len(suggestions) >= limit:
                        break
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting user suggestions: {str(e)}")
            return []

# Create service instance
user_discovery_service = UserDiscoveryService()
