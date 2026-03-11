# Events API

This document covers the events management endpoints in the Sahana Backend API.

## Overview

The Events API allows users to create, discover, update, and manage events. It supports filtering, pagination, and RSVP functionality.

## Endpoints

### Get All Events

**Endpoint:** `GET /api/events`

**Query Parameters:**

- `category` (optional): Filter by event category
- `city` (optional): Filter by city
- `state` (optional): Filter by state
- `is_online` (optional): Filter online events only (boolean)
- `creator_email` (optional): Filter by creator email
- `start_date` (optional): Events starting from this date (ISO format)
- `end_date` (optional): Events ending before this date (ISO format)
- `cursor` (optional): Base64 encoded cursor for pagination
- `page_size` (optional): Items per page (1-100, default: 12)
- `direction` (optional): Pagination direction ("next" or "prev", default: "next")

**Example Request:**

```
GET /api/events?category=technology&city=San+Francisco&page_size=10
```

**Response (cursor-paginated):**

```json
{
  "items": [...],
  "pagination": {
    "next_cursor": "eyJzdGFydFRpbWUiOi...",
    "prev_cursor": null,
    "has_next": true,
    "has_previous": false,
    "page_size": 12
  }
}
```

### Get Event by ID

**Endpoint:** `GET /api/events/{event_id}`

**Response:**

```json
{
  "id": "event_123",
  "title": "Tech Meetup 2025",
  "description": "Join us for networking and tech talks",
  "category": "technology",
  "date_time": "2025-07-15T18:00:00Z",
  "location": {
    "address": "123 Tech Street, San Francisco, CA",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "is_online": false,
  "max_attendees": 50,
  "current_attendees": 15,
  "tags": ["technology", "networking"],
  "created_by": "user123",
  "created_at": "2025-06-28T10:00:00Z",
  "updated_at": "2025-06-28T10:00:00Z",
  "rsvp_status": "going"
}
```

### Create Event

**Endpoint:** `POST /api/events/new`

**Authentication:** Required

**Request Body:**

```json
{
  "title": "Tech Meetup 2025",
  "description": "Join us for networking and tech talks",
  "category": "technology",
  "date_time": "2025-07-15T18:00:00Z",
  "location": {
    "address": "123 Tech Street, San Francisco, CA",
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "is_online": false,
  "max_attendees": 50,
  "tags": ["technology", "networking"]
}
```

**Response:** Same as Get Event by ID

### Update Event

**Endpoint:** `PUT /api/events/{event_id}`

**Authentication:** Required (event creator only)

**Request Body:** Same as Create Event

### Delete Event

**Endpoint:** `DELETE /api/events/{event_id}`

**Authentication:** Required (event creator only)

**Response:**

```json
{
  "message": "Event deleted successfully"
}
```

### Get User's Created Events

**Endpoint:** `GET /api/events/me/created`

**Authentication:** Required

**Query Parameters:** Cursor pagination parameters (`cursor`, `page_size`, `direction`)

### Get User's RSVP'd Events

**Endpoint:** `GET /api/events/me/rsvped`

**Authentication:** Required

**Query Parameters:** Cursor pagination parameters (`cursor`, `page_size`, `direction`)

### Get User's Organized Events

**Endpoint:** `GET /api/events/me/organized`

**Authentication:** Required

### Get User's Moderated Events

**Endpoint:** `GET /api/events/me/moderated`

**Authentication:** Required

### Get User's Interested Events

**Endpoint:** `GET /api/events/me/interested`

**Authentication:** Required

### Get Nearby Events

**Endpoint:** `GET /api/events/location/nearby`

**Authentication:** Not required

**Query Parameters:** `city` (required), `state` (required), cursor pagination parameters

### Archive Event

**Endpoint:** `PATCH /api/events/{event_id}/archive`

**Authentication:** Required (event creator only)

### Unarchive Event

**Endpoint:** `PATCH /api/events/{event_id}/unarchive`

**Authentication:** Required (event creator only)

## Event Categories

Supported event categories:

- `technology`
- `business`
- `arts`
- `sports`
- `health`
- `education`
- `food`
- `music`
- `networking`
- `other`

## Event Status in Responses

When authenticated, events include an `rsvp_status` field:

- `null`: Not RSVP'd
- `"going"`: User has RSVP'd to attend
- `"interested"`: User marked as interested (if implemented)

## Location Object

The location object contains:

```json
{
  "address": "Human-readable address",
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

For online events, location can be null or contain virtual meeting details.

## Error Responses

### Event Not Found

```json
{
  "detail": "Event not found"
}
```

### Unauthorized Event Action

```json
{
  "detail": "You don't have permission to modify this event"
}
```

### Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "date_time"],
      "msg": "Event date cannot be in the past",
      "type": "value_error"
    }
  ]
}
```
