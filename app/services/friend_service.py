from app.services.friend_request_service import FriendRequestService
from app.services.friend_management_service import FriendManagementService
from app.services.user_discovery_service import UserDiscoveryService
from app.repositories.friends import FriendRepository
from app.repositories.users import UserRepository
from app.models.friend import FriendRequestWithProfile, FriendProfile, UserSearchResult
from app.utils.logger import get_service_logger
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class FriendService:
    """
    Facade service that combines all friend-related functionality.
    Maintains backward compatibility while delegating to specialized services.
    """
    
    def __init__(self, friend_repo: Optional[FriendRepository] = None, user_repo: Optional[UserRepository] = None):
        """Initialize service with repository dependencies (supports dependency injection)"""
        # Initialize specialized services with appropriate repositories
        friend_repo_instance = friend_repo or FriendRepository()
        self.friend_request_service = FriendRequestService(friend_repo_instance, user_repo)
        self.friend_management_service = FriendManagementService(friend_repo_instance, user_repo)
        self.user_discovery_service = UserDiscoveryService(friend_repo_instance, user_repo)
        self.logger = get_service_logger(__name__)

    # Friend Request Operations (delegate to FriendRequestService)
    async def send_friend_request(self, sender_email: str, receiver_id: str) -> Dict[str, Any]:
        """Send a friend request from sender to receiver"""
        return await self.friend_request_service.send_friend_request(sender_email, receiver_id)

    async def get_friend_requests(self, user_email: str) -> Dict[str, List[FriendRequestWithProfile]]:
        """Get all friend requests for a user (both sent and received)"""
        return await self.friend_request_service.get_friend_requests(user_email)

    async def respond_to_friend_request(self, request_id: str, accept: bool, user_email: str) -> Dict[str, Any]:
        """Accept or reject a friend request"""
        return await self.friend_request_service.respond_to_friend_request(request_id, accept, user_email)

    async def cancel_friend_request(self, request_id: str, user_email: str) -> Dict[str, Any]:
        """Cancel a sent friend request"""
        return await self.friend_request_service.cancel_friend_request(request_id, user_email)

    # Friend Management Operations (delegate to FriendManagementService)
    async def get_friends_list(self, user_email: str) -> List[FriendProfile]:
        """Get the list of friends for a user"""
        return await self.friend_management_service.get_friends_list(user_email)

    async def get_friendship_status(self, current_user_email: str, user_id: str) -> Dict[str, Any]:
        """Get the friendship status between current user and another user"""
        return await self.friend_management_service.get_friendship_status(current_user_email, user_id)

    async def remove_friendship(self, user_email: str, friend_email: str) -> Dict[str, Any]:
        """Remove a friendship between two users"""
        return await self.friend_management_service.remove_friendship(user_email, friend_email)

    # User Discovery Operations (delegate to UserDiscoveryService)
    async def search_users(self, search_term: str, user_email: str, limit: int = 20) -> List[UserSearchResult]:
        """Search for users and include friendship status - includes input validation"""
        # Business logic: validate search term
        if not search_term or not search_term.strip():
            return []
        
        return await self.user_discovery_service.search_users(search_term.strip(), user_email, limit)

    async def get_user_suggestions(self, user_email: str, limit: int = 10) -> List[UserSearchResult]:
        """Get friend suggestions based on mutual friends, interests, etc."""
        return await self.user_discovery_service.get_user_suggestions(user_email, limit)

    # Data Transformation Methods (centralized response formatting)
    def format_friend_requests_response(self, requests: Dict[str, List[FriendRequestWithProfile]]) -> Dict[str, List[Dict[str, Any]]]:
        """Format friend requests for API response - centralized transformation"""
        try:
            received_dicts = []
            for req in requests["received"]:
                received_dicts.append(self._format_friend_request_dict(req))
            
            sent_dicts = []
            for req in requests["sent"]:
                sent_dicts.append(self._format_friend_request_dict(req))
            
            return {
                "received": received_dicts,
                "sent": sent_dicts
            }
        except Exception as e:
            self.logger.error(f"Error formatting friend requests response: {e}")
            return {"received": [], "sent": []}

    def format_friends_list_response(self, friends: List[FriendProfile]) -> List[Dict[str, Any]]:
        """Format friends list for API response - centralized transformation (no events_created/events_attended)"""
        try:
            friends_dicts = []
            for friend in friends:
                friends_dicts.append({
                    "id": friend.id,
                    "name": friend.name,
                    "email": friend.email,
                    "bio": friend.bio,
                    "profile_picture": friend.profile_picture,
                    "location": friend.location,
                    "interests": friend.interests,
                    "created_at": friend.created_at.isoformat() if friend.created_at else None
                })
            return friends_dicts
        except Exception as e:
            self.logger.error(f"Error formatting friends list response: {e}")
            return []

    def format_user_search_response(self, search_results: List[UserSearchResult]) -> List[Dict[str, Any]]:
        """Format user search results for API response - centralized transformation"""
        try:
            results_dicts = []
            for result in search_results:
                results_dicts.append({
                    "id": result.id,
                    "name": result.name,
                    "email": result.email,
                    "bio": result.bio,
                    "profile_picture": result.profile_picture,
                    "location": result.location,
                    "interests": result.interests,
                    "friendship_status": result.friendship_status
                })
            return results_dicts
        except Exception as e:
            self.logger.error(f"Error formatting user search response: {e}")
            return []

    def _format_friend_request_dict(self, req: FriendRequestWithProfile) -> Dict[str, Any]:
        """Private helper method to format a single friend request"""
        return {
            "id": req.id,
            "sender": {
                "id": req.sender.id,
                "name": req.sender.name,
                "email": req.sender.email,
                "bio": req.sender.bio,
                "profile_picture": req.sender.profile_picture,
                "location": req.sender.location,
                "interests": req.sender.interests
            },
            "receiver": {
                "id": req.receiver.id,
                "name": req.receiver.name,
                "email": req.receiver.email,
                "bio": req.receiver.bio,
                "profile_picture": req.receiver.profile_picture,
                "location": req.receiver.location,
                "interests": req.receiver.interests
            },
            "status": req.status,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "updated_at": req.updated_at.isoformat() if req.updated_at else None
        }

# Create service instance (maintains backward compatibility)
friend_service = FriendService()
