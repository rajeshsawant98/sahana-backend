from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from app.services.friend_service import friend_service
from app.models.friend import (
    FriendRequestCreate, 
    FriendRequestResponse, 
    FriendRequestWithProfile, 
    FriendProfile, 
    UserSearchResult
)
from app.auth.roles import user_only
from typing import List, Dict, Any

friend_router = APIRouter()

# -------------------- Request Models --------------------

class SendFriendRequestModel(BaseModel):
    receiver_id: str

class RespondToRequestModel(BaseModel):
    accept: bool

# -------------------- Routes --------------------

@friend_router.post("/request")
async def send_friend_request(
    request: SendFriendRequestModel, 
    current_user: dict = Depends(user_only)
) -> Dict[str, Any]:
    """Send a friend request to another user
    
    Note: receiver_id should be the email address of the user to send a request to
    """
    try:
        result = friend_service.send_friend_request(
            sender_email=current_user["email"],
            receiver_id=request.receiver_id
        )
        
        if result["success"]:
            return {
                "message": result["message"],
                "request_id": result.get("request_id")
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send friend request: {str(e)}")

@friend_router.get("/requests")
async def get_friend_requests(
    current_user: dict = Depends(user_only)
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all friend requests for the current user (both sent and received)"""
    try:
        requests = friend_service.get_friend_requests(current_user["email"])
        return friend_service.format_friend_requests_response(requests)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get friend requests: {str(e)}")

@friend_router.post("/accept/{request_id}")
async def accept_friend_request(
    request_id: str,
    current_user: dict = Depends(user_only)
) -> Dict[str, str]:
    """Accept a friend request"""
    try:
        result = friend_service.respond_to_friend_request(
            request_id=request_id,
            accept=True,
            user_email=current_user["email"]
        )
        
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept friend request: {str(e)}")

@friend_router.post("/reject/{request_id}")
async def reject_friend_request(
    request_id: str,
    current_user: dict = Depends(user_only)
) -> Dict[str, str]:
    """Reject a friend request"""
    try:
        result = friend_service.respond_to_friend_request(
            request_id=request_id,
            accept=False,
            user_email=current_user["email"]
        )
        
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject friend request: {str(e)}")

@friend_router.delete("/request/{request_id}")
async def cancel_friend_request(
    request_id: str,
    current_user: dict = Depends(user_only)
) -> Dict[str, str]:
    """Cancel a sent friend request"""
    try:
        result = friend_service.cancel_friend_request(
            request_id=request_id,
            user_email=current_user["email"]
        )
        
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel friend request: {str(e)}")

@friend_router.get("/list")
async def get_friends_list(
    current_user: dict = Depends(user_only)
) -> List[Dict[str, Any]]:
    """Get the list of friends for the current user"""
    try:
        friends = friend_service.get_friends_list(current_user["email"])
        return friend_service.format_friends_list_response(friends)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get friends list: {str(e)}")

@friend_router.get("/search")
async def search_users(
    q: str = Query(..., description="Search term for user name or email"),
    limit: int = Query(20, description="Maximum number of results to return"),
    current_user: dict = Depends(user_only)
) -> List[Dict[str, Any]]:
    """Search for users to send friend requests"""
    try:
        search_results = friend_service.search_users(
            search_term=q,
            user_email=current_user["email"],
            limit=limit
        )
        
        return friend_service.format_user_search_response(search_results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")

# Additional utility endpoint for getting friendship status between two users
@friend_router.get("/status/{user_id}")
async def get_friendship_status(
    user_id: str,
    current_user: dict = Depends(user_only)
) -> Dict[str, str]:
    """Get the friendship status between current user and another user"""
    try:
        result = friend_service.get_friendship_status(current_user["email"], user_id)
        
        if result["success"]:
            return {"friendship_status": result["friendship_status"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get friendship status: {str(e)}")
