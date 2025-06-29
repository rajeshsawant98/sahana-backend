# Sahana Backend API Documentation

## Overview

The Sahana Backend provides a comprehensive RESTful API for event management, user authentication, friend systems, and admin operations. All endpoints use JSON for request and response bodies and are fully implemented and production-ready.

## Base URL

```
https://your-sahana-backend.com/api
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Token Refresh

Tokens expire after a set period. Use the refresh endpoint to obtain new tokens without re-authentication.

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [User Management](#user-management)
3. [Friend System](#friend-system)
4. [Event Management](#event-management)
5. [Event RSVP](#event-rsvp)
6. [Event Roles](#event-roles)
7. [Event Archive](#event-archive)
8. [Location-Based Events](#location-based-events)
9. [Event Ingestion](#event-ingestion)
10. [Admin Operations](#admin-operations)
11. [Error Responses](#error-responses)
12. [Response Codes](#response-codes)

---

## Authentication Endpoints

### Register User

**POST** `/auth/signup`

Register a new user account.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Response:** `201 Created`

```json
{
  "message": "User registered successfully",
  "userId": "user123",
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses:**

- `400 Bad Request` - Invalid input data
- `409 Conflict` - Email already exists

---

### Login User

**POST** `/auth/login`

Authenticate user and receive access tokens.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`

```json
{
  "message": "Login successful",
  "userId": "user123",
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "interests": ["technology", "music"]
  }
}
```

**Error Responses:**

- `400 Bad Request` - Missing credentials
- `401 Unauthorized` - Invalid credentials

---

### Refresh Token

**POST** `/auth/refresh`

Refresh access token using refresh token.

**Request Body:**

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `200 OK`

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid or expired refresh token

---

## User Management

### Get User Profile

**GET** `/users/profile`

Get current user's profile information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "userId": "user123",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "interests": ["technology", "music"],
  "city": "San Francisco",
  "state": "CA",
  "createdAt": "2025-06-01T10:00:00Z"
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `404 Not Found` - User not found

---

### Update User Profile

**PUT** `/users/profile`

Update current user's profile information.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "firstName": "John",
  "lastName": "Smith",
  "city": "Los Angeles",
  "state": "CA",
  "bio": "Tech enthusiast and event organizer"
}
```

**Response:** `200 OK`

```json
{
  "message": "Profile updated successfully",
  "user": {
    "userId": "user123",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Smith",
    "city": "Los Angeles",
    "state": "CA",
    "bio": "Tech enthusiast and event organizer"
  }
}
```

**Error Responses:**

- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Invalid token

---

### Update User Interests

**PUT** `/users/interests`

Update user's interests/preferences.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "interests": ["technology", "music", "sports", "art"]
}
```

**Response:** `200 OK`

```json
{
  "message": "Interests updated successfully",
  "interests": ["technology", "music", "sports", "art"]
}
```

**Error Responses:**

- `400 Bad Request` - Invalid interests format
- `401 Unauthorized` - Invalid token

---

### Get All Users (Admin)

**GET** `/users`

Get paginated list of all users (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**

- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)

**Response:** `200 OK`

```json
{
  "users": [
    {
      "userId": "user123",
      "email": "user@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "city": "San Francisco",
      "state": "CA",
      "createdAt": "2025-06-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 150,
    "total_pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not admin user

---

## Friend System

### Send Friend Request

**POST** `/friends/request`

Send a friend request to another user.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "friendEmail": "friend@example.com"
}
```

**Response:** `201 Created`

```json
{
  "message": "Friend request sent successfully",
  "requestId": "req123",
  "friendEmail": "friend@example.com",
  "status": "pending"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid email or self-request
- `401 Unauthorized` - Invalid token
- `404 Not Found` - Friend user not found
- `409 Conflict` - Request already exists

---

### Accept Friend Request

**POST** `/friends/accept`

Accept a pending friend request.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "requesterEmail": "requester@example.com"
}
```

**Response:** `200 OK`

```json
{
  "message": "Friend request accepted",
  "friendship": {
    "friendEmail": "requester@example.com",
    "status": "accepted",
    "createdAt": "2025-06-28T10:00:00Z"
  }
}
```

**Error Responses:**

- `400 Bad Request` - Invalid email
- `401 Unauthorized` - Invalid token
- `404 Not Found` - Request not found

---

### Decline Friend Request

**POST** `/friends/decline`

Decline a pending friend request.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "requesterEmail": "requester@example.com"
}
```

**Response:** `200 OK`

```json
{
  "message": "Friend request declined"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid email
- `401 Unauthorized` - Invalid token
- `404 Not Found` - Request not found

---

### Remove Friend

**DELETE** `/friends/remove`

Remove an existing friendship.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "friendEmail": "friend@example.com"
}
```

**Response:** `200 OK`

```json
{
  "message": "Friend removed successfully"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid email
- `401 Unauthorized` - Invalid token
- `404 Not Found` - Friendship not found

---

### Get Friends List

**GET** `/friends`

Get current user's friends list.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "friends": [
    {
      "email": "friend1@example.com",
      "firstName": "Jane",
      "lastName": "Smith",
      "status": "accepted",
      "friendsSince": "2025-06-01T10:00:00Z"
    }
  ],
  "count": 5
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token

---

### Get Pending Friend Requests

**GET** `/friends/pending`

Get pending friend requests received by current user.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "pending_requests": [
    {
      "requesterEmail": "requester@example.com",
      "requesterName": "John Doe",
      "requestedAt": "2025-06-28T10:00:00Z"
    }
  ],
  "count": 2
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token

---

### Get Sent Friend Requests

**GET** `/friends/sent`

Get friend requests sent by current user.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "sent_requests": [
    {
      "friendEmail": "friend@example.com",
      "friendName": "Jane Smith",
      "sentAt": "2025-06-28T10:00:00Z",
      "status": "pending"
    }
  ],
  "count": 1
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token

---

### Check Friendship Status

**GET** `/friends/status/{userId}`

Check friendship status with a specific user.

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `userId`: Target user's ID

**Response:** `200 OK`

```json
{
  "status": "accepted",
  "relationship": "friends",
  "since": "2025-06-01T10:00:00Z"
}
```

**Possible Status Values:**

- `none` - No relationship
- `pending` - Request sent/received
- `accepted` - Friends
- `blocked` - Blocked relationship

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `404 Not Found` - User not found

---

## Event Management

### Create Event

**POST** `/events/new`

Create a new event.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "eventName": "Tech Meetup 2025",
  "description": "Join us for an exciting tech discussion",
  "location": {
    "address": "123 Tech Street",
    "city": "San Francisco",
    "state": "CA",
    "zipCode": "94102"
  },
  "startTime": "2025-07-15T18:00:00Z",
  "duration": 120,
  "categories": ["technology", "networking"],
  "isOnline": false,
  "joinLink": "",
  "imageUrl": "https://example.com/event-image.jpg"
}
```

**Response:** `201 Created`

```json
{
  "message": "Event created successfully",
  "eventId": "event123"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid event data
- `401 Unauthorized` - Invalid token

---

### Get All Events

**GET** `/events`

Get paginated list of all active events with optional filtering.

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)
- `city` (optional): Filter by city
- `state` (optional): Filter by state
- `category` (optional): Filter by category
- `is_online` (optional): Filter by online events (true/false)
- `creator_email` (optional): Filter by creator email
- `start_date` (optional): Filter by start date (ISO format)
- `end_date` (optional): Filter by end date (ISO format)

**Response:** `200 OK`

**Without Pagination:**

```json
{
  "events": [
    {
      "eventId": "event123",
      "eventName": "Tech Meetup 2025",
      "description": "Join us for an exciting tech discussion",
      "location": {
        "address": "123 Tech Street",
        "city": "San Francisco",
        "state": "CA",
        "zipCode": "94102"
      },
      "startTime": "2025-07-15T18:00:00Z",
      "duration": 120,
      "categories": ["technology", "networking"],
      "isOnline": false,
      "imageUrl": "https://example.com/event-image.jpg",
      "createdBy": "user123",
      "createdByEmail": "organizer@example.com",
      "createdAt": "2025-06-28T10:00:00Z",
      "rsvpList": ["user1@example.com", "user2@example.com"],
      "organizers": ["organizer@example.com"],
      "moderators": []
    }
  ]
}
```

**With Pagination:**

```json
{
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 250,
    "total_pages": 25,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Get Event by ID

**GET** `/events/{eventId}`

Get detailed information about a specific event.

**Path Parameters:**

- `eventId`: Event ID

**Response:** `200 OK`

```json
{
  "eventId": "event123",
  "eventName": "Tech Meetup 2025",
  "description": "Join us for an exciting tech discussion",
  "location": {
    "address": "123 Tech Street",
    "city": "San Francisco",
    "state": "CA",
    "zipCode": "94102"
  },
  "startTime": "2025-07-15T18:00:00Z",
  "duration": 120,
  "categories": ["technology", "networking"],
  "isOnline": false,
  "joinLink": "",
  "imageUrl": "https://example.com/event-image.jpg",
  "createdBy": "user123",
  "createdByEmail": "organizer@example.com",
  "organizers": ["organizer@example.com"],
  "moderators": [],
  "createdAt": "2025-06-28T10:00:00Z",
  "rsvpList": ["user1@example.com", "user2@example.com"],
  "rsvpCount": 2
}
```

**Error Responses:**

- `404 Not Found` - Event not found

---

### Update Event

**PUT** `/events/{eventId}`

Update an existing event (creator only).

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Request Body:**

```json
{
  "eventName": "Updated Tech Meetup 2025",
  "description": "Updated description",
  "location": {
    "address": "456 New Tech Street",
    "city": "San Francisco",
    "state": "CA",
    "zipCode": "94102"
  },
  "startTime": "2025-07-15T19:00:00Z",
  "duration": 150
}
```

**Response:** `200 OK`

```json
{
  "message": "Event updated successfully"
}
```

**Error Responses:**

- `400 Bad Request` - Invalid event data
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not event creator
- `404 Not Found` - Event not found

---

### Delete Event

**DELETE** `/events/{eventId}`

Delete an event (creator only).

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Response:** `200 OK`

```json
{
  "message": "Event deleted successfully"
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not event creator
- `404 Not Found` - Event not found

---

### Get User's Created Events

**GET** `/events/me/created`

Get events created by the current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

**Without Pagination:**

```json
{
  "message": "Events fetched successfully",
  "events": [...]
}
```

**With Pagination:**

```json
{
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 15,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `404 Not Found` - No events found

---

### Get User's RSVP'd Events

**GET** `/events/me/rsvped`

Get events the current user has RSVP'd to.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

```json
{
  "message": "RSVP'd events fetched",
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 8,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `404 Not Found` - No RSVP'd events found

---

### Get User's Organized Events

**GET** `/events/me/organized`

Get events the current user is an organizer for.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

```json
{
  "message": "Organized events fetched",
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 5,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `404 Not Found` - No organized events found

---

### Get User's Moderated Events

**GET** `/events/me/moderated`

Get events the current user is a moderator for.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

```json
{
  "message": "Moderated events fetched",
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 3,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `404 Not Found` - No moderated events found

---

## Event RSVP

### RSVP to Event

**POST** `/events/{eventId}/rsvp`

RSVP to an event.

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Response:** `200 OK`

```json
{
  "message": "Successfully RSVP'd to event",
  "rsvp_status": "going",
  "event": {
    "id": "event123",
    "title": "Tech Meetup 2025",
    "current_attendees": 16
  }
}
```

**Error Responses:**

- `400 Bad Request` - Cannot RSVP to archived event
- `401 Unauthorized` - Invalid token
- `404 Not Found` - Event not found
- `409 Conflict` - Already RSVP'd to this event

---

### Cancel RSVP

**DELETE** `/events/{eventId}/rsvp`

Cancel RSVP to an event.

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Response:** `200 OK`

```json
{
  "message": "RSVP cancelled successfully",
  "rsvp_status": null,
  "event": {
    "id": "event123",
    "title": "Tech Meetup 2025",
    "current_attendees": 15
  }
}
```

**Error Responses:**

- `400 Bad Request` - You have not RSVP'd to this event
- `401 Unauthorized` - Invalid token
- `404 Not Found` - Event not found

---

### Get Event RSVPs

**GET** `/events/{eventId}/rsvps`

Get the RSVP list for an event.

**Path Parameters:**

- `eventId`: Event ID

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (default: 10, max: 100)

**Response (Paginated):** `200 OK`

```json
{
  "items": [
    {
      "user_email": "user1@example.com"
    },
    {
      "user_email": "user2@example.com"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 25,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

**Response (Non-paginated):** `200 OK`

```json
{
  "rsvp_list": [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
  ],
  "total_count": 3
}
```

**Error Responses:**

- `404 Not Found` - Event not found

---

## Event Roles

### Update Event Organizers

**PATCH** `/events/{eventId}/organizers`

Update the list of event organizers (creator only).

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Request Body:**

```json
{
  "organizerEmails": [
    "organizer1@example.com",
    "organizer2@example.com"
  ]
}
```

**Response:** `200 OK`

```json
{
  "message": "Organizers updated",
  "organizerIds": ["user123", "user456"],
  "skipped": []
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not event creator
- `404 Not Found` - Event not found

---

### Update Event Moderators

**PATCH** `/events/{eventId}/moderators`

Update the list of event moderators (organizer only).

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Request Body:**

```json
{
  "moderatorEmails": [
    "moderator1@example.com",
    "moderator2@example.com"
  ]
}
```

**Response:** `200 OK`

```json
{
  "message": "Moderators updated",
  "moderatorIds": ["user789", "user101"],
  "skipped": []
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not event organizer
- `404 Not Found` - Event not found

---

## Event Archive

### Archive Event

**PATCH** `/events/{eventId}/archive`

Archive an event (soft delete) - creator only.

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Request Body:**

```json
{
  "reason": "Event cancelled due to weather"
}
```

**Response:** `200 OK`

```json
{
  "message": "Event archived successfully (Note: This event has not ended yet)",
  "archived_by": "user@example.com",
  "reason": "Event cancelled due to weather"
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not event creator
- `404 Not Found` - Event not found

---

### Unarchive Event

**PATCH** `/events/{eventId}/unarchive`

Restore an archived event - creator only.

**Headers:** `Authorization: Bearer <token>`

**Path Parameters:**

- `eventId`: Event ID

**Response:** `200 OK`

```json
{
  "message": "Event restored successfully"
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not event creator
- `404 Not Found` - Event not found

---

### Get User's Archived Events

**GET** `/events/me/archived`

Get current user's archived events.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

**Without Pagination:**

```json
{
  "archived_events": [
    {
      "eventId": "event123",
      "eventName": "Cancelled Tech Meetup",
      "isArchived": true,
      "archivedAt": "2025-06-28T10:00:00Z",
      "archivedBy": "user@example.com",
      "archiveReason": "Event cancelled due to weather"
    }
  ],
  "count": 5
}
```

**With Pagination:**

```json
{
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 5,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token

---

### Get All Archived Events (Admin)

**GET** `/events/archived`

Get all archived events across the system (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**

- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

```json
{
  "archived_events": [...],
  "count": 150,
  "message": "Retrieved 150 archived events",
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 150,
    "total_pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not admin user

---

### Bulk Archive Past Events (Admin)

**POST** `/events/archive/past-events`

Automatically archive all events that have ended (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`

```json
{
  "message": "Successfully archived 25 past events",
  "archived_count": 25
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not admin user

---

## Location-Based Events

### Get Nearby Events

**GET** `/events/location/nearby`

Get community events near a specific location.

**Query Parameters:**

- `city` (required): City name
- `state` (required): State name
- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

**Without Pagination:**

```json
{
  "events": [...],
  "count": 15
}
```

**With Pagination:**

```json
{
  "events": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 15,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Responses:**

- `400 Bad Request` - Missing city or state

---

### Get External Events

**GET** `/events/location/external`

Get external events (from Ticketmaster, Eventbrite) for a location.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**

- `city` (required): City name
- `state` (required): State name
- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (max: 100)

**Response:** `200 OK`

```json
{
  "events": [
    {
      "eventId": "ext123",
      "eventName": "Concert at Stadium",
      "description": "Amazing live music experience",
      "location": {
        "city": "San Francisco",
        "state": "CA"
      },
      "startTime": "2025-07-20T20:00:00Z",
      "origin": "external",
      "source": "ticketmaster",
      "categories": ["music", "entertainment"]
    }
  ],
  "count": 8,
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 8,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**Error Responses:**

- `400 Bad Request` - Missing city or state
- `401 Unauthorized` - Invalid token

---

## Event Ingestion

### Fetch Ticketmaster Events (Admin)

**POST** `/events/fetch-ticketmaster-events`

Fetch and ingest events from Ticketmaster API (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Request Body:**

```json
{
  "city": "San Francisco",
  "state": "CA"
}
```

**Response:** `200 OK`

```json
{
  "message": "15 new events ingested, 3 skipped.",
  "sample": [
    {
      "eventName": "Sample Concert",
      "location": {
        "city": "San Francisco",
        "state": "CA"
      },
      "startTime": "2025-07-20T20:00:00Z"
    }
  ]
}
```

**Error Responses:**

- `400 Bad Request` - Missing city or state
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not admin user

---

### Ingest Events for All Cities (Admin)

**POST** `/events/ingest/all`

Ingest events for all user locations (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`

```json
{
  "message": "Ingestion completed for all cities",
  "cities_processed": 25,
  "total_events_ingested": 450,
  "processing_time": "45 seconds"
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not admin user

---

## Admin Operations

### Get All Users (Admin)

**GET** `/admin/users`

Get paginated list of all users (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**

- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)

**Response:** `200 OK`

```json
{
  "users": [
    {
      "userId": "user123",
      "email": "user@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "city": "San Francisco",
      "state": "CA",
      "createdAt": "2025-06-01T10:00:00Z",
      "lastLogin": "2025-06-28T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 1500,
    "total_pages": 150,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Not admin user

---

## Error Responses

### Standard Error Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details (optional)",
    "timestamp": "2025-06-28T10:00:00Z"
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_TOKEN` | JWT token is invalid or expired |
| `MISSING_PERMISSION` | User lacks required permissions |
| `VALIDATION_ERROR` | Request data validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVER_ERROR` | Internal server error |

---

## Response Codes

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| `200` | OK | Successful GET, PUT, PATCH, DELETE |
| `201` | Created | Successful POST (resource created) |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource conflict (duplicate) |
| `422` | Unprocessable Entity | Validation errors |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

---

## Pagination

### Pagination Parameters

All paginated endpoints support these parameters:

- `page`: Page number (starts from 1)
- `page_size`: Number of items per page (max: 100)

### Pagination Response Format

```json
{
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 250,
    "total_pages": 25,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General Endpoints:** 100 requests per minute per user
- **Authentication Endpoints:** 10 requests per minute per IP
- **Admin Endpoints:** 200 requests per minute per admin user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Examples

### Complete User Workflow

1. **Register:**

```bash
curl -X POST https://api.sahana.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123","firstName":"John","lastName":"Doe"}'
```

2. **Create Event:**

```bash
curl -X POST https://api.sahana.com/events/new \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"eventName":"Tech Meetup","location":{"city":"SF","state":"CA"},"startTime":"2025-07-15T18:00:00Z","duration":120}'
```

3. **RSVP to Event:**

```bash
curl -X POST https://api.sahana.com/events/event123/rsvp \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Complete Friend Workflow

1. **Send Friend Request:**

```bash
curl -X POST https://api.sahana.com/friends/request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"friendEmail":"friend@example.com"}'
```

2. **Accept Friend Request:**

```bash
curl -X POST https://api.sahana.com/friends/accept \
  -H "Authorization: Bearer FRIEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requesterEmail":"user@example.com"}'
```

---

*Last Updated: June 28, 2025*
*API Version: 1.0*
