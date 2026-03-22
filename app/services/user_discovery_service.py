from app.repositories.friends import FriendRepository
from app.repositories.users import UserRepository
from app.models.friend import UserSearchResult
from app.utils.logger import get_service_logger
from typing import List, Dict, Any, Optional, Literal

class UserDiscoveryService:
    """Service for discovering and searching users"""
    
    def __init__(self, friend_repo: Optional[FriendRepository] = None, user_repo: Optional[UserRepository] = None):
        self.friend_repo = friend_repo or FriendRepository()
        self.user_repo = user_repo or UserRepository()
        self.logger = get_service_logger(__name__)

    async def search_users(self, search_term: str, user_email: str, limit: int = 20) -> List[UserSearchResult]:
        """Search for users and include friendship status"""
        try:
            # Validate current user exists
            current_user = await self.user_repo.get_by_email(user_email)
            if not current_user:
                return []
            
            # Use user repository to search for users
            users_data = await self.user_repo.search_users(search_term, user_email, limit)
            
            search_results = []
            for user_data in users_data:
                # Get friendship status using existing repository methods
                request = await self.friend_repo.find_request_between_users(user_email, user_data.get("email", ""), ["accepted"])
                if request:
                    friendship_status = "friends"
                else:
                    # Check for pending requests
                    pending_request = await self.friend_repo.find_request_between_users(
                        user_email,
                        user_data.get("email", ""),
                        ["pending"],
                    )
                    if pending_request:
                        if pending_request["sender_id"] == user_email:
                            friendship_status = "pending_sent"
                        else:
                            friendship_status = "pending_received"
                    else:
                        friendship_status = "none"
                
                # Ensure friendship_status is one of the valid literal values
                valid_status: Literal["friends", "pending_sent", "pending_received", "none"] = "none"
                if friendship_status in ["friends", "pending_sent", "pending_received", "none"]:
                    valid_status = friendship_status  # type: ignore
                
                user_result = UserSearchResult(
                    id=user_data.get("id", user_data.get("email", "")),  # Use ID or email as fallback
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

    async def get_user_suggestions(self, user_email: str, limit: int = 10) -> List[UserSearchResult]:
        """Get friend suggestions based on shared interests.
        Single query — joins out already-connected users instead of N+1 checks.
        """
        try:
            current_user = await self.user_repo.get_by_email(user_email)
            if not current_user:
                return []

            user_interests = current_user.get("interests") or []
            if not user_interests:
                return []

            from sqlalchemy import text
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT u.email, u.name, u.bio, u.profile_picture,
                           u.interests, u.latitude, u.longitude,
                           u.city, u.state, u.country, u.formatted_address, u.location_name
                    FROM users u
                    WHERE u.email != :me
                      AND u.interests && :interests
                      AND NOT EXISTS (
                          SELECT 1 FROM friend_requests fr
                          WHERE (fr.sender_id = :me AND fr.receiver_id = u.email)
                             OR (fr.receiver_id = :me AND fr.sender_id = u.email)
                      )
                    LIMIT :limit
                """), {
                    "me": user_email,
                    "interests": user_interests,
                    "limit": limit,
                })
                rows = result.fetchall()

            from app.repositories.users.user_repository import _row_to_user_dict
            suggestions = []
            for row in rows:
                u = _row_to_user_dict(row)
                suggestions.append(UserSearchResult(
                    id=u.get("email", ""),
                    name=u.get("name", ""),
                    email=u.get("email", ""),
                    bio=u.get("bio"),
                    profile_picture=u.get("profile_picture"),
                    location=u.get("location"),
                    interests=u.get("interests", []),
                    friendship_status="none",
                ))
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting user suggestions: {str(e)}")
            return []

# Create service instance
user_discovery_service = UserDiscoveryService()
