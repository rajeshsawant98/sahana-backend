"""
Integration test for friend system endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, Mock

client = TestClient(app)

class TestFriendSystemIntegration:
    
    @patch('app.auth.roles.user_only')
    @patch('app.services.friend_service.friend_service.send_friend_request')
    def test_send_friend_request_endpoint(self, mock_send_request, mock_auth):
        """Test the send friend request endpoint"""
        # Setup auth mock
        mock_auth.return_value = {"email": "sender@example.com", "role": "user"}
        
        # Setup service mock
        mock_send_request.return_value = {
            "success": True,
            "message": "Friend request sent successfully",
            "request_id": "test-123"
        }
        
        # Make request
        response = client.post(
            "/api/friends/request",
            json={"receiver_id": "receiver@example.com"},
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Friend request sent successfully"
        assert data["request_id"] == "test-123"

    @patch('app.auth.roles.user_only')
    @patch('app.services.friend_service.friend_service.get_friend_requests')
    def test_get_friend_requests_endpoint(self, mock_get_requests, mock_auth):
        """Test the get friend requests endpoint"""
        # Setup auth mock
        mock_auth.return_value = {"email": "user@example.com", "role": "user"}
        
        # Setup service mock
        from app.models.friend import FriendRequestWithProfile, FriendProfile
        from datetime import datetime
        
        mock_sender = FriendProfile(
            id="sender@example.com",
            name="Sender User",
            email="sender@example.com"
        )
        
        mock_receiver = FriendProfile(
            id="user@example.com", 
            name="Current User",
            email="user@example.com"
        )
        
        mock_request = FriendRequestWithProfile(
            id="test-123",
            sender=mock_sender,
            receiver=mock_receiver,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        mock_get_requests.return_value = {
            "received": [mock_request],
            "sent": []
        }
        
        # Make request
        response = client.get(
            "/api/friends/requests",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["received"]) == 1
        assert len(data["sent"]) == 0
        assert data["received"][0]["sender"]["name"] == "Sender User"

    @patch('app.auth.roles.user_only')
    @patch('app.services.friend_service.friend_service.respond_to_friend_request')
    def test_accept_friend_request_endpoint(self, mock_respond, mock_auth):
        """Test the accept friend request endpoint"""
        # Setup auth mock
        mock_auth.return_value = {"email": "user@example.com", "role": "user"}
        
        # Setup service mock
        mock_respond.return_value = {
            "success": True,
            "message": "Friend request accepted successfully"
        }
        
        # Make request
        response = client.post(
            "/api/friends/accept/test-123",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Friend request accepted successfully"

    @patch('app.auth.roles.user_only')
    @patch('app.services.friend_service.friend_service.cancel_friend_request')
    def test_cancel_friend_request_endpoint(self, mock_cancel, mock_auth):
        """Test the cancel friend request endpoint"""
        # Setup auth mock
        mock_auth.return_value = {"email": "user@example.com", "role": "user"}
        
        # Setup service mock
        mock_cancel.return_value = {
            "success": True,
            "message": "Friend request cancelled successfully"
        }
        
        # Make request
        response = client.delete(
            "/api/friends/request/test-123",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Friend request cancelled successfully"

    @patch('app.auth.roles.user_only')
    @patch('app.services.friend_service.friend_service.get_friends_list')
    def test_get_friends_list_endpoint(self, mock_get_friends, mock_auth):
        """Test the get friends list endpoint"""
        # Setup auth mock
        mock_auth.return_value = {"email": "user@example.com", "role": "user"}
        
        # Setup service mock
        from app.models.friend import FriendProfile
        
        mock_friend = FriendProfile(
            id="friend@example.com",
            name="Friend User",
            email="friend@example.com",
            bio="A good friend"
        )
        
        mock_get_friends.return_value = [mock_friend]
        
        # Make request
        response = client.get(
            "/api/friends/list",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Friend User"
        assert data[0]["email"] == "friend@example.com"

    @patch('app.auth.roles.user_only')
    @patch('app.services.friend_service.friend_service.search_users')
    def test_search_users_endpoint(self, mock_search, mock_auth):
        """Test the search users endpoint"""
        # Setup auth mock
        mock_auth.return_value = {"email": "user@example.com", "role": "user"}
        
        # Setup service mock
        from app.models.friend import UserSearchResult
        
        mock_result = UserSearchResult(
            id="found@example.com",
            name="Found User",
            email="found@example.com",
            friendship_status="none"
        )
        
        mock_search.return_value = [mock_result]
        
        # Make request
        response = client.get(
            "/api/friends/search?q=found&limit=10",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Found User"
        assert data[0]["friendship_status"] == "none"

    def test_search_users_missing_query_param(self):
        """Test search users endpoint with missing query parameter"""
        response = client.get(
            "/api/friends/search",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Should fail because q parameter is required
        assert response.status_code == 422

    @patch('app.auth.roles.user_only')
    def test_search_users_empty_query(self, mock_auth):
        """Test search users endpoint with empty query"""
        # Setup auth mock
        mock_auth.return_value = {"email": "user@example.com", "role": "user"}
        
        # Make request with empty query
        response = client.get(
            "/api/friends/search?q=",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Should return empty list for empty query
        assert response.status_code == 200
        data = response.json()
        assert data == []

if __name__ == "__main__":
    pytest.main([__file__])
