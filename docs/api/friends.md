# Friends API

This document covers the friend system endpoints in the Sahana Backend API.

## Overview

The Friends API handles user connections, allowing users to send, accept, reject, and manage friend requests, as well as view their friends list.

## Endpoints

### Send Friend Request

**Endpoint:** `POST /api/friends/request`

**Authentication:** Required

**Request Body:**

```json
{
  "receiver_id": "user@example.com"
}
```

**Response:**

```json
{
  "message": "Friend request sent successfully",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Get Friend Requests

**Endpoint:** `GET /api/friends/requests`

**Authentication:** Required

**Response:**

```json
{
  "received": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sender": {
        "id": "sender@example.com",
        "name": "Jane Smith",
        "email": "sender@example.com",
        "bio": "Loves tech events",
        "profile_picture": "https://example.com/photo.jpg",
        "location": {
          "address": "San Francisco, CA",
          "latitude": 37.7749,
          "longitude": -122.4194
        },
        "interests": ["technology", "networking"]
      },
      "receiver": {
        "id": "user@example.com",
        "name": "John Doe",
        "email": "user@example.com",
        "bio": "Event organizer",
        "profile_picture": "https://example.com/photo2.jpg",
        "location": null,
        "interests": ["events", "community"]
      },
      "status": "pending",
      "created_at": "2025-06-28T10:00:00Z",
      "updated_at": null
    }
  ],
  "sent": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "sender": {
        "id": "user@example.com",
        "name": "John Doe",
        "email": "user@example.com",
        "bio": "Event organizer",
        "profile_picture": "https://example.com/photo2.jpg",
        "location": null,
        "interests": ["events", "community"]
      },
      "receiver": {
        "id": "friend@example.com",
        "name": "Alice Johnson",
        "email": "friend@example.com",
        "bio": "Community builder",
        "profile_picture": "https://example.com/photo3.jpg",
        "location": {
          "address": "New York, NY",
          "latitude": 40.7128,
          "longitude": -74.0060
        },
        "interests": ["community", "volunteering"]
      },
      "status": "pending",
      "created_at": "2025-06-28T09:30:00Z",
      "updated_at": null
    }
  ]
}
```

### Accept Friend Request

**Endpoint:** `POST /api/friends/accept/{request_id}`

**Authentication:** Required

**Response:**

```json
{
  "message": "Friend request accepted successfully"
}
```

### Reject Friend Request

**Endpoint:** `POST /api/friends/reject/{request_id}`

**Authentication:** Required

**Response:**

```json
{
  "message": "Friend request rejected successfully"
}
```

### Cancel Friend Request

**Endpoint:** `DELETE /api/friends/request/{request_id}`

**Authentication:** Required

**Response:**

```json
{
  "message": "Friend request cancelled successfully"
}
```

### Get Friends List

**Endpoint:** `GET /api/friends/list`

**Authentication:** Required

**Response:**

```json
[
  {
    "id": "friend1@example.com",
    "name": "Jane Smith",
    "email": "friend1@example.com",
    "bio": "Loves tech events",
    "profile_picture": "https://example.com/photo.jpg",
    "location": {
      "address": "San Francisco, CA",
      "latitude": 37.7749,
      "longitude": -122.4194
    },
    "interests": ["technology", "networking"],
    "events_created": 3,
    "events_attended": 15,
    "created_at": "2025-01-15T10:00:00Z"
  },
  {
    "id": "friend2@example.com",
    "name": "Bob Wilson",
    "email": "friend2@example.com",
    "bio": "Community organizer",
    "profile_picture": "https://example.com/photo4.jpg",
    "location": {
      "address": "Austin, TX",
      "latitude": 30.2672,
      "longitude": -97.7431
    },
    "interests": ["community", "music"],
    "events_created": 7,
    "events_attended": 8,
    "created_at": "2025-02-20T14:30:00Z"
  }
]
```

### Search Users

**Endpoint:** `GET /api/friends/search`

**Authentication:** Required

**Query Parameters:**

- `q` (required): Search term for user name or email
- `limit` (optional): Maximum number of results to return (default: 20)

**Example:** `GET /api/friends/search?q=john&limit=10`

**Response:**

```json
[
  {
    "id": "john@example.com",
    "name": "John Smith",
    "email": "john@example.com",
    "bio": "Tech enthusiast",
    "profile_picture": "https://example.com/photo5.jpg",
    "location": {
      "address": "Seattle, WA",
      "latitude": 47.6062,
      "longitude": -122.3321
    },
    "interests": ["technology", "startups"],
    "friendship_status": "none"
  },
  {
    "id": "johnny@example.com",
    "name": "Johnny Doe",
    "email": "johnny@example.com",
    "bio": "Event photographer",
    "profile_picture": "https://example.com/photo6.jpg",
    "location": null,
    "interests": ["photography", "events"],
    "friendship_status": "pending_sent"
  }
]
```

### Get Friendship Status

**Endpoint:** `GET /api/friends/status/{user_id}`

**Authentication:** Required

**Response:**

```json
{
  "friendship_status": "friends"
}
```

## Friendship Status Values

The `friendship_status` field can have the following values:

- `"none"`: No relationship exists between the users
- `"friends"`: Users are friends (request was accepted)
- `"pending_sent"`: Current user has sent a friend request to the other user
- `"pending_received"`: Current user has received a friend request from the other user

## Friend Request Workflow

1. **Search for Users**: Use the search endpoint to find users by name or email
2. **Send Request**: Send a friend request to a user using their user ID
3. **Receive Requests**: View incoming and outgoing friend requests
4. **Respond to Requests**: Accept or reject incoming friend requests
5. **Manage Requests**: Cancel outgoing friend requests if needed
6. **View Friends**: See the list of accepted friends

## Data Models

### Friend Profile

Contains public information about a user in the context of friendships:

```json
{
  "id": "user@example.com",
  "name": "User Name",
  "email": "user@example.com",
  "bio": "User bio (optional)",
  "profile_picture": "URL to profile image (optional)",
  "location": {
    "address": "City, State",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "interests": ["interest1", "interest2"],
  "events_created": 5,
  "events_attended": 12,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Friend Request

Represents a friend request between two users:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender": {}, // Friend Profile object
  "receiver": {}, // Friend Profile object
  "status": "pending|accepted|rejected",
  "created_at": "2025-06-28T10:00:00Z",
  "updated_at": "2025-06-28T11:00:00Z"
}
```

## Error Responses

### Friend Request Errors

**Already Friends:**

```json
{
  "detail": "Already friends"
}
```

**Friend Request Already Pending:**

```json
{
  "detail": "Friend request already pending"
}
```

**Cannot Send to Self:**

```json
{
  "detail": "Cannot send friend request to yourself"
}
```

**User Not Found:**

```json
{
  "detail": "Receiver not found"
}
```

### Authorization Errors

**Not Authorized to Respond:**

```json
{
  "detail": "Not authorized to respond to this request"
}
```

**Not Authorized to Cancel:**

```json
{
  "detail": "Not authorized to cancel this request"
}
```

### Request State Errors

**Request Not Found:**

```json
{
  "detail": "Friend request not found"
}
```

**Request No Longer Pending:**

```json
{
  "detail": "Friend request is no longer pending"
}
```

**Can Only Cancel Pending:**

```json
{
  "detail": "Can only cancel pending friend requests"
}
```

## Integration with Other APIs

Friend information is used in:

- **Event API**: Show which friends are attending events
- **User API**: Display mutual friends and social connections
- **Notification System**: Send notifications for friend requests and acceptances

## Cache Considerations

The friend system includes several caching points:

- **Friend Lists**: Cache friends list to reduce database queries
- **Friendship Status**: Cache relationship status for search results
- **Friend Requests**: Cache pending requests for quick access

Cache invalidation occurs when:

- Friend requests are sent, accepted, rejected, or cancelled
- User profiles are updated
- Friend relationships change

## Privacy and Security

### Privacy Settings

- Friend lists are only visible to the user themselves
- Search results show limited public profile information
- Friend requests include full profile information only for pending/accepted relationships

### Security Measures

- Authentication required for all friend endpoints
- Authorization checks ensure users can only manage their own requests
- Rate limiting prevents spam friend requests
- Input validation prevents malicious data injection

## Best Practices

### For Frontend Implementation

1. **Debounce Search**: Implement search debouncing to reduce API calls
2. **Optimistic UI**: Update UI immediately on user actions, revert on errors
3. **Real-time Updates**: Consider WebSocket integration for real-time friend notifications
4. **Pagination**: Implement pagination for large friend lists
5. **Error Handling**: Provide clear error messages to users

### For Backend Integration

1. **Batch Operations**: Consider batch endpoints for bulk friend operations
2. **Background Processing**: Use queues for sending friend request notifications
3. **Data Consistency**: Ensure friend relationships are bidirectional
4. **Cleanup**: Regularly clean up old rejected friend requests
5. **Analytics**: Track friend system usage for improvements
