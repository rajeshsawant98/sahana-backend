"""
Integration test for friend system endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.roles import user_only
from unittest.mock import patch, Mock, AsyncMock

client = TestClient(app)


# ─── Auth override fixtures ────────────────────────────────────────────────────

def _override_sender():
    return {"email": "sender@example.com", "role": "user"}

def _override_user():
    return {"email": "user@example.com", "role": "user"}


class TestFriendSystemIntegration:

    def test_send_friend_request_endpoint(self):
        """Test the send friend request endpoint"""
        app.dependency_overrides[user_only] = _override_sender
        try:
            with patch('app.services.friend_service.friend_service.send_friend_request') as mock_send_request:
                mock_send_request.return_value = {
                    "success": True,
                    "message": "Friend request sent successfully",
                    "request_id": "test-123"
                }
                response = client.post(
                    "/api/friends/request",
                    json={"receiver_id": "receiver@example.com"},
                    headers={"Authorization": "Bearer fake-token"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Friend request sent successfully"
        assert data["request_id"] == "test-123"

    def test_get_friend_requests_endpoint(self):
        """Test the get friend requests endpoint"""
        app.dependency_overrides[user_only] = _override_user
        try:
            with patch('app.services.friend_service.friend_service.get_friend_requests') as mock_get_requests:
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

                response = client.get(
                    "/api/friends/requests",
                    headers={"Authorization": "Bearer fake-token"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data["received"]) == 1
        assert len(data["sent"]) == 0
        assert data["received"][0]["sender"]["name"] == "Sender User"

    def test_accept_friend_request_endpoint(self):
        """Test the accept friend request endpoint"""
        app.dependency_overrides[user_only] = _override_user
        try:
            with patch('app.services.friend_service.friend_service.respond_to_friend_request') as mock_respond:
                mock_respond.return_value = {
                    "success": True,
                    "message": "Friend request accepted successfully"
                }
                response = client.post(
                    "/api/friends/accept/test-123",
                    headers={"Authorization": "Bearer fake-token"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Friend request accepted successfully"

    def test_cancel_friend_request_endpoint(self):
        """Test the cancel friend request endpoint"""
        app.dependency_overrides[user_only] = _override_user
        try:
            with patch('app.services.friend_service.friend_service.cancel_friend_request') as mock_cancel:
                mock_cancel.return_value = {
                    "success": True,
                    "message": "Friend request cancelled successfully"
                }
                response = client.delete(
                    "/api/friends/request/test-123",
                    headers={"Authorization": "Bearer fake-token"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Friend request cancelled successfully"

    def test_get_friends_list_endpoint(self):
        """Test the get friends list endpoint"""
        app.dependency_overrides[user_only] = _override_user
        try:
            with patch('app.services.friend_service.friend_service.get_friends_list') as mock_get_friends:
                from app.models.friend import FriendProfile
                mock_friend = FriendProfile(
                    id="friend@example.com",
                    name="Friend User",
                    email="friend@example.com",
                    bio="A good friend"
                )
                mock_get_friends.return_value = [mock_friend]

                response = client.get(
                    "/api/friends/list",
                    headers={"Authorization": "Bearer fake-token"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Friend User"
        assert data[0]["email"] == "friend@example.com"

    def test_search_users_endpoint(self):
        """Test the search users endpoint"""
        app.dependency_overrides[user_only] = _override_user
        try:
            with patch('app.services.friend_service.friend_service.search_users') as mock_search:
                from app.models.friend import UserSearchResult
                mock_result = UserSearchResult(
                    id="found@example.com",
                    name="Found User",
                    email="found@example.com",
                    friendship_status="none"
                )
                mock_search.return_value = [mock_result]

                response = client.get(
                    "/api/friends/search?q=found&limit=10",
                    headers={"Authorization": "Bearer fake-token"}
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Found User"
        assert data[0]["friendship_status"] == "none"

    def test_search_users_missing_query_param(self):
        """Test search users endpoint with missing query parameter"""
        # Auth runs before param validation, so override auth to get 422
        app.dependency_overrides[user_only] = _override_user
        try:
            response = client.get(
                "/api/friends/search",
                headers={"Authorization": "Bearer fake-token"}
            )
        finally:
            app.dependency_overrides.clear()
        # Should fail because q parameter is required
        assert response.status_code == 422

    def test_search_users_empty_query(self):
        """Test search users endpoint with empty query"""
        app.dependency_overrides[user_only] = _override_user
        try:
            response = client.get(
                "/api/friends/search?q=",
                headers={"Authorization": "Bearer fake-token"}
            )
        finally:
            app.dependency_overrides.clear()

        # Should return empty list for empty query
        assert response.status_code == 200
        data = response.json()
        assert data == []


if __name__ == "__main__":
    pytest.main([__file__])
