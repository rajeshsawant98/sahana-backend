# Users API

This document covers user management endpoints in the Sahana Backend API.

## Overview

The Users API handles user profiles, registration, and user-related operations.

## Endpoints

### Get Current User Profile

**Endpoint:** `GET /users/me`

**Authentication:** Required

**Response:**

```json
{
  "id": "user123",
  "email": "user@example.com",
  "name": "John Doe",
  "bio": "Tech enthusiast and event organizer",
  "location": {
    "address": "San Francisco, CA",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "profile_picture": "https://example.com/photo.jpg",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-06-28T10:00:00Z",
  "preferences": {
    "email_notifications": true,
    "push_notifications": false
  }
}
```

### Update User Profile

**Endpoint:** `PUT /users/me`

**Authentication:** Required

**Request Body:**

```json
{
  "name": "John Doe",
  "bio": "Updated bio here",
  "location": {
    "address": "New York, NY",
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "preferences": {
    "email_notifications": true,
    "push_notifications": true
  }
}
```

**Response:** Same as Get Current User Profile

### Get User by ID

**Endpoint:** `GET /users/{user_id}`

**Authentication:** Not required (public profile)

**Response:**

```json
{
  "id": "user123",
  "name": "John Doe",
  "bio": "Tech enthusiast and event organizer",
  "profile_picture": "https://example.com/photo.jpg",
  "created_at": "2025-01-15T10:00:00Z",
  "events_created": 5,
  "events_attended": 12
}
```

Note: Public profile shows limited information compared to the user's own profile.

### Upload Profile Picture

**Endpoint:** `POST /users/me/avatar`

**Authentication:** Required

**Request:** Multipart form data with image file

**Response:**

```json
{
  "message": "Profile picture updated successfully",
  "profile_picture": "https://example.com/new-photo.jpg"
}
```

### Delete User Account

**Endpoint:** `DELETE /users/me`

**Authentication:** Required

**Response:**

```json
{
  "message": "Account deleted successfully"
}
```

## User Profile Fields

### Required Fields

- `email`: User's email address (unique)
- `name`: Display name

### Optional Fields

- `bio`: User biography/description
- `location`: User's location information
- `profile_picture`: URL to profile image
- `preferences`: User notification preferences

### Read-Only Fields

- `id`: Unique user identifier
- `created_at`: Account creation timestamp
- `updated_at`: Last profile update timestamp
- `events_created`: Number of events created
- `events_attended`: Number of events attended

## Location Object

User location follows the same format as event locations:

```json
{
  "address": "Human-readable address",
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

## User Preferences

Configurable user preferences:

```json
{
  "email_notifications": true,
  "push_notifications": false,
  "event_reminders": true,
  "marketing_emails": false
}
```

## Privacy and Visibility

### Public Information

- Name
- Bio
- Profile picture
- Number of events created/attended
- Join date

### Private Information

- Email address
- Exact location (only city/region shown publicly)
- Notification preferences
- RSVP history details

## Error Responses

### User Not Found

```json
{
  "detail": "User not found",
  "error_code": "USER_NOT_FOUND"
}
```

### Invalid Profile Data

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### Profile Picture Upload Error

```json
{
  "detail": "File size too large. Maximum size is 5MB",
  "error_code": "FILE_TOO_LARGE"
}
```

## Integration with Other APIs

User information is included in:
- Event responses (creator information)
- RSVP lists (attendee information)
- Event creation/updates (ownership validation)
