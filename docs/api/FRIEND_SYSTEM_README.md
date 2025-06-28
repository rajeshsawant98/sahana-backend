# Friend System Implementation

This document describes the implementation of the friend system MVP for the Sahana backend.

## 📁 Files Created

### Backend Files

- **`app/models/friend.py`** - Data models for friend requests and user profiles
- **`app/repositories/friend_repository.py`** - Database operations for friend system
- **`app/services/friend_service.py`** - Business logic for friend operations
- **`app/routes/friend_routes.py`** - API endpoints for friend functionality
- **`app/test/test_friend_system.py`** - Unit tests for friend service
- **`app/test/test_friend_integration.py`** - Integration tests for friend API

### Documentation Files

- **`docs/api/friends.md`** - Complete API documentation for friend endpoints
- **Updated `docs/api/users.md`** - Added friend system integration information

## 🔌 API Endpoints

The friend system provides the following endpoints under `/api/friends`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/request` | Send a friend request |
| `GET` | `/requests` | Get pending friend requests |
| `POST` | `/accept/{request_id}` | Accept a friend request |
| `POST` | `/reject/{request_id}` | Reject a friend request |
| `DELETE` | `/request/{request_id}` | Cancel a sent friend request |
| `GET` | `/list` | Get friends list |
| `GET` | `/search` | Search users to befriend |
| `GET` | `/status/{user_id}` | Get friendship status |

## 🗄️ Database Structure

### Friend Requests Collection

The system uses a `friend_requests` collection in Firestore with the following structure:

```json
{
  "id": "uuid-string",
  "sender_id": "sender@example.com",
  "receiver_id": "receiver@example.com", 
  "status": "pending|accepted|rejected",
  "created_at": "2025-06-28T10:00:00Z",
  "updated_at": "2025-06-28T11:00:00Z"
}
```

### Users Collection Integration

The friend system integrates with the existing `users` collection to:
- Search for users by name or email
- Retrieve user profile information
- Display friend profiles

## 🔄 Friend Request Workflow

1. **Search**: User searches for other users by name or email
2. **Send Request**: User sends a friend request to another user
3. **Receive Notification**: Receiver gets a pending friend request
4. **Respond**: Receiver can accept or reject the request
5. **Friendship Established**: If accepted, users become friends
6. **Management**: Users can view friends list and cancel pending requests

## 🔒 Security & Authorization

- All endpoints require authentication (JWT token)
- Users can only manage their own friend requests
- Authorization checks prevent unauthorized access to requests
- Input validation prevents malicious data

## 🧪 Testing

### Unit Tests (`test_friend_system.py`)

Tests the friend service layer with mocked dependencies:
- Send friend request (success, failures, edge cases)
- Accept/reject friend requests
- Cancel friend requests  
- Get friends list
- Search users

### Integration Tests (`test_friend_integration.py`)

Tests the complete API endpoints with mocked authentication:
- All API endpoints with various scenarios
- Error handling and edge cases
- Request/response validation

## 📋 Data Models

### Core Models

- **`FriendRequest`** - Represents a friend request between users
- **`FriendProfile`** - Public user profile for friend contexts
- **`UserSearchResult`** - User search results with friendship status
- **`FriendRequestWithProfile`** - Friend request with full user profiles

### Request/Response Models

- **`FriendRequestCreate`** - Request to send friend request
- **`FriendRequestResponse`** - Response to friend request (accept/reject)

## 🔧 Key Features

### Smart Search
- Search users by name or email
- Shows friendship status in search results
- Excludes current user from results

### Request Management
- Send requests with validation
- Accept/reject with authorization checks
- Cancel pending requests
- Prevent duplicate requests

### Friends List
- View all accepted friends
- Rich profile information
- Sortable and filterable

### Status Tracking
- Track friendship status between any two users
- Real-time status updates
- Bidirectional relationship management

## 🚀 Usage Examples

### Send Friend Request
```bash
curl -X POST /api/friends/request \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"receiver_id": "friend@example.com"}'
```

### Search Users
```bash
curl -X GET "/api/friends/search?q=john&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Get Friends List
```bash
curl -X GET /api/friends/list \
  -H "Authorization: Bearer <token>"
```

## 🔮 Future Enhancements

### Phase 2 Features
- Real-time notifications for friend requests
- Mutual friends display
- Friend activity feeds
- Group friend management
- Friend recommendations

### Technical Improvements
- Redis caching for friendship status
- WebSocket integration for real-time updates
- Background job processing for notifications
- Analytics and metrics tracking

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Auth Errors**: Verify JWT token is valid and included
3. **Database Errors**: Check Firestore permissions and connectivity
4. **Validation Errors**: Verify request body format matches API spec

### Debugging

- Check application logs for detailed error messages
- Use test endpoints to verify functionality
- Validate Firestore collections and indexes
- Test with different user roles and permissions

## 📊 Performance Considerations

- **Indexing**: Firestore queries are optimized with proper indexes
- **Pagination**: Large friend lists support pagination
- **Caching**: Friendship status can be cached for performance
- **Rate Limiting**: Prevents spam friend requests

This implementation provides a solid foundation for the friend system and can be extended with additional features as needed.
