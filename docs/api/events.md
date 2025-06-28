# Events API

This document covers the events management endpoints in the Sahana Backend API.

## Overview

The Events API allows users to create, discover, update, and manage events. It supports filtering, pagination, and RSVP functionality.

## Endpoints

### Get All Events

**Endpoint:** `GET /events/`

**Query Parameters:**

- `category` (optional): Filter by event category
- `location` (optional): Filter by location
- `date_from` (optional): Events starting from this date (ISO format)
- `date_to` (optional): Events ending before this date (ISO format)
- `online` (optional): Filter online events only (boolean)
- `search` (optional): Search in title and description
- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (1-100, default: 10)

**Example Request:**

```
GET /events/?category=technology&location=San Francisco&page=1&page_size=10
```

**Response (without pagination):**

```json
{
  "events": [
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
      "rsvp_status": null
    }
  ]
}
```

### Get Event by ID

**Endpoint:** `GET /events/{event_id}`

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

**Endpoint:** `POST /events/`

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

**Endpoint:** `PUT /events/{event_id}`

**Authentication:** Required (event creator only)

**Request Body:** Same as Create Event

### Delete Event

**Endpoint:** `DELETE /events/{event_id}`

**Authentication:** Required (event creator only)

**Response:**

```json
{
  "message": "Event deleted successfully"
}
```

### Get User's Created Events

**Endpoint:** `GET /events/me/created`

**Authentication:** Required

**Query Parameters:**

- `page` (optional): Page number
- `page_size` (optional): Items per page

### Get User's RSVP'd Events

**Endpoint:** `GET /events/me/rsvped`

**Authentication:** Required

**Query Parameters:**

- `page` (optional): Page number
- `page_size` (optional): Items per page

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
  "detail": "Event not found",
  "error_code": "EVENT_NOT_FOUND"
}
```

### Unauthorized Event Action

```json
{
  "detail": "You don't have permission to modify this event",
  "error_code": "INSUFFICIENT_PERMISSIONS"
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
