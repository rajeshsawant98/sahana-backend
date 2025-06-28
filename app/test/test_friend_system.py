import pytest
import pytest
from app.services.friend_service import friend_service
from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository
from unittest.mock import Mock, patch

class TestFriendService:
    
    def setup_method(self):
        """Setup test data before each test - now all users use email as ID"""
        self.sender_email = "sender@example.com"
        self.receiver_email = "receiver@example.com"  # Changed from receiver_id to receiver_email
        self.test_request_id = "test-request-123"
        
        # Mock user data - email is now the ID for all users
        self.mock_sender = {
            "id": self.sender_email,  # Email is the ID
            "name": "Sender User",
            "email": self.sender_email,
            "bio": "Test sender",
            "profile_picture": None,
            "location": None,
            "interests": ["testing"]
        }
        
        self.mock_receiver = {
            "id": self.receiver_email,  # Email is the ID
            "name": "Receiver User", 
            "email": self.receiver_email,
            "bio": "Test receiver",
            "profile_picture": None,
            "location": None,
            "interests": ["testing"]
        }

    @patch.object(FriendRepository, 'create_friend_request')
    @patch.object(FriendRepository, 'get_friend_request_by_users')
    @patch.object(UserRepository, 'get_by_email')
    def test_send_friend_request_success(self, mock_get_by_email, 
                                       mock_get_friend_request, mock_create_request):
        """Test successful friend request sending"""
        # Setup mocks - now both calls are to get_by_email
        mock_get_by_email.side_effect = [self.mock_sender, self.mock_receiver]
        mock_get_friend_request.return_value = None  # No existing request
        mock_create_request.return_value = self.test_request_id
        
        # Test
        result = friend_service.send_friend_request(self.sender_email, self.receiver_email)
        
        # Assertions
        assert result["success"] is True
        assert result["message"] == "Friend request sent successfully"
        assert result["request_id"] == self.test_request_id
        
        # Verify mock calls - both should be get_by_email calls
        assert mock_get_by_email.call_count == 2
        mock_get_by_email.assert_any_call(self.sender_email)
        mock_get_by_email.assert_any_call(self.receiver_email)
        mock_get_friend_request.assert_called_once_with(self.sender_email, self.receiver_email)
        mock_create_request.assert_called_once_with(self.sender_email, self.receiver_email)

    @patch.object(UserRepository, 'get_by_email')
    def test_send_friend_request_sender_not_found(self, mock_get_by_email):
        """Test friend request when sender doesn't exist"""
        # Setup mocks
        mock_get_by_email.return_value = None
        
        # Test
        result = friend_service.send_friend_request(self.sender_email, self.receiver_email)
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Sender not found"

    @patch.object(UserRepository, 'get_by_email')
    def test_send_friend_request_receiver_not_found(self, mock_get_by_email):
        """Test friend request when receiver doesn't exist"""
        # Setup mocks - sender exists, receiver doesn't
        mock_get_by_email.side_effect = [self.mock_sender, None]
        
        # Test
        result = friend_service.send_friend_request(self.sender_email, self.receiver_email)
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Receiver not found"

    @patch.object(FriendRepository, 'get_friend_request_by_users')
    @patch.object(UserRepository, 'get_by_email')
    def test_send_friend_request_already_friends(self, mock_get_by_email, 
                                                mock_get_friend_request):
        """Test friend request when users are already friends"""
        # Setup mocks
        mock_get_by_email.side_effect = [self.mock_sender, self.mock_receiver]
        mock_get_friend_request.return_value = {"status": "accepted"}
        
        # Test
        result = friend_service.send_friend_request(self.sender_email, self.receiver_email)
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Already friends"

    @patch.object(FriendRepository, 'get_friend_request_by_users')
    @patch.object(UserRepository, 'get_by_email')
    def test_send_friend_request_already_pending(self, mock_get_by_email, 
                                                mock_get_friend_request):
        """Test friend request when request is already pending"""
        # Setup mocks
        mock_get_by_email.side_effect = [self.mock_sender, self.mock_receiver]
        mock_get_friend_request.return_value = {"status": "pending"}
        
        # Test
        result = friend_service.send_friend_request(self.sender_email, self.receiver_email)
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Friend request already pending"

    @patch.object(FriendRepository, 'update_friend_request_status')
    @patch.object(FriendRepository, 'get_request_by_id')
    @patch.object(UserRepository, 'get_by_email')
    def test_accept_friend_request_success(self, mock_get_by_email, mock_get_request, mock_update_status):
        """Test successful friend request acceptance"""
        # Setup mocks
        mock_get_by_email.return_value = self.mock_receiver  # Return receiver user data
        
        mock_request = {
            "id": self.test_request_id,
            "sender_id": self.sender_email,
            "receiver_id": self.receiver_email,
            "status": "pending"
        }
        mock_get_request.return_value = mock_request
        mock_update_status.return_value = True
        
        # Test (using receiver email but checking against receiver ID)
        result = friend_service.respond_to_friend_request(self.test_request_id, True, self.receiver_email)
        
        # Assertions
        assert result["success"] is True
        assert result["message"] == "Friend request accepted successfully"
        
        # Verify mock calls
        mock_get_by_email.assert_called_once_with(self.receiver_email)
        mock_get_request.assert_called_once_with(self.test_request_id)
        mock_update_status.assert_called_once_with(self.test_request_id, "accepted")

    @patch.object(FriendRepository, 'get_request_by_id')
    @patch.object(UserRepository, 'get_by_email')
    def test_accept_friend_request_not_found(self, mock_get_by_email, mock_get_request):
        """Test accepting non-existent friend request"""
        # Setup mocks
        mock_get_by_email.return_value = self.mock_receiver  # Return receiver user data
        mock_get_request.return_value = None
        
        # Test
        result = friend_service.respond_to_friend_request(self.test_request_id, True, self.receiver_email)
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Friend request not found"

    @patch.object(FriendRepository, 'get_request_by_id')
    @patch.object(UserRepository, 'get_by_email')
    def test_accept_friend_request_unauthorized(self, mock_get_by_email, mock_get_request):
        """Test accepting friend request by unauthorized user"""
        # Setup mocks - create a different user for the unauthorized test
        wrong_user = {
            "id": "wrong@example.com",
            "name": "Wrong User",
            "email": "wrong@example.com"
        }
        mock_get_by_email.return_value = wrong_user
        
        mock_request = {
            "id": self.test_request_id,
            "sender_id": self.sender_email,
            "receiver_id": self.receiver_email,
            "status": "pending"
        }
        mock_get_request.return_value = mock_request
        
        # Test with wrong user
        result = friend_service.respond_to_friend_request(self.test_request_id, True, "wrong@example.com")
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Not authorized to respond to this request"

    @patch.object(FriendRepository, 'delete_friend_request')
    @patch.object(FriendRepository, 'get_request_by_id')
    @patch.object(UserRepository, 'get_by_email')
    def test_cancel_friend_request_success(self, mock_get_by_email, mock_get_request, mock_delete_request):
        """Test successful friend request cancellation"""
        # Setup mocks
        mock_get_by_email.return_value = self.mock_sender  # Return sender user data
        
        mock_request = {
            "id": self.test_request_id,
            "sender_id": self.sender_email,
            "receiver_id": self.receiver_email,
            "status": "pending"
        }
        mock_get_request.return_value = mock_request
        mock_delete_request.return_value = True
        
        # Test
        result = friend_service.cancel_friend_request(self.test_request_id, self.sender_email)
        
        # Assertions
        assert result["success"] is True
        assert result["message"] == "Friend request cancelled successfully"
        
        # Verify mock calls
        mock_get_by_email.assert_called_once_with(self.sender_email)
        mock_get_request.assert_called_once_with(self.test_request_id)
        mock_delete_request.assert_called_once_with(self.test_request_id)

    @patch.object(FriendRepository, 'get_friends_for_user')
    @patch.object(UserRepository, 'get_by_email')
    def test_get_friends_list_success(self, mock_get_by_email, mock_get_friends):
        """Test getting friends list"""
        # Setup mocks
        mock_get_by_email.return_value = self.mock_sender  # Return the sender user data
        
        mock_friends_data = [
            {
                "id": "friend1@example.com",
                "name": "Friend One",
                "email": "friend1@example.com",
                "bio": "Test friend 1",
                "profile_picture": None,
                "location": None,
                "interests": ["testing"],
                "created_at": None
            }
        ]
        mock_get_friends.return_value = mock_friends_data
        
        # Test
        result = friend_service.get_friends_list(self.sender_email)
        
        # Assertions
        assert len(result) == 1
        assert result[0].name == "Friend One"
        assert result[0].email == "friend1@example.com"
        
        # Verify mock calls
        mock_get_by_email.assert_called_once_with(self.sender_email)
        mock_get_friends.assert_called_once_with(self.sender_email)  # sender_email is the ID

    @patch.object(FriendRepository, 'search_users')
    @patch.object(FriendRepository, 'get_friendship_status')
    @patch.object(UserRepository, 'get_by_email')
    def test_search_users_success(self, mock_get_by_email, mock_get_status, mock_search_users):
        """Test searching for users"""
        # Setup mocks
        mock_get_by_email.return_value = self.mock_sender  # Return the sender user data
        
        mock_users_data = [
            {
                "id": "found@example.com",
                "name": "Found User",
                "email": "found@example.com",
                "bio": "Found user bio",
                "profile_picture": None,
                "location": None,
                "interests": ["testing"]
            }
        ]
        mock_search_users.return_value = mock_users_data
        mock_get_status.return_value = "none"
        
        # Test
        result = friend_service.search_users("Found", self.sender_email, 20)
        
        # Assertions
        assert len(result) == 1
        assert result[0].name == "Found User"
        assert result[0].friendship_status == "none"
        
        # Verify mock calls
        mock_get_by_email.assert_called_once_with(self.sender_email)
        mock_search_users.assert_called_once_with("Found", self.sender_email, 20)  # sender_email is the ID
        mock_get_status.assert_called_once_with(self.sender_email, "found@example.com")

if __name__ == "__main__":
    pytest.main([__file__])
