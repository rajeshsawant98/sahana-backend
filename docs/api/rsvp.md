# RSVP API

This document covers the RSVP (Répondez s'il vous plaît) system for events in the Sahana Backend API.

## Overview

The RSVP system allows users to:

- RSVP to events they want to attend
- Cancel their RSVP
- View RSVPs for events
- Track RSVP status across the platform

## Endpoints

### RSVP to Event

**Endpoint:** `POST /events/{event_id}/rsvp`

**Authentication:** Required

**Request Body:** (Optional)

```json
{
  "note": "Looking forward to this event!"
}
```

**Response:**

```json
{
  "message": "Successfully RSVP'd to event",
  "rsvp_status": "going",
  "event": {
    "id": "event_123",
    "title": "Tech Meetup 2025",
    "current_attendees": 16
  }
}
```

### Cancel RSVP

**Endpoint:** `DELETE /events/{event_id}/rsvp`

**Authentication:** Required

**Response:**

```json
{
  "message": "RSVP cancelled successfully",
  "rsvp_status": null,
  "event": {
    "id": "event_123",
    "title": "Tech Meetup 2025",
    "current_attendees": 15
  }
}
```

### Get Event RSVPs

**Endpoint:** `GET /events/{event_id}/rsvps`

**Query Parameters:**

- `page` (optional): Page number
- `page_size` (optional): Items per page (default: 10)

**Response:**

```json
{
  "items": [
    {
      "user_id": "user123",
      "user_name": "John Doe",
      "user_profile_picture": "https://example.com/photo.jpg",
      "rsvp_date": "2025-06-28T10:00:00Z",
      "note": "Looking forward to this event!"
    }
  ],
  "total_count": 15,
  "page": 1,
  "page_size": 10,
  "total_pages": 2,
  "has_next": true,
  "has_previous": false
}
```

### Get User's RSVP'd Events

**Endpoint:** `GET /events/me/rsvped`

**Authentication:** Required

**Query Parameters:**

- `page` (optional): Page number
- `page_size` (optional): Items per page
- `upcoming` (optional): Filter upcoming events only (boolean)

**Response:**

```json
{
  "items": [
    {
      "id": "event_123",
      "title": "Tech Meetup 2025",
      "date_time": "2025-07-15T18:00:00Z",
      "location": {
        "address": "123 Tech Street, San Francisco, CA"
      },
      "rsvp_date": "2025-06-28T10:00:00Z",
      "rsvp_status": "going"
    }
  ],
  "total_count": 5,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

## RSVP Rules and Validation

### Maximum Attendees

Events can have a maximum attendee limit. RSVP will fail if:

- Event has reached maximum capacity
- Event has been cancelled or deleted

### Event Timing

- Users can RSVP to future events
- RSVP to past events may be restricted
- RSVP cutoff time can be set (e.g., 1 hour before event)

### User Permissions

- Users must be authenticated to RSVP
- Users can only RSVP once per event
- Event creators are automatically RSVP'd to their own events

## RSVP Status Values

- `null`: User has not RSVP'd
- `"going"`: User has confirmed attendance
- `"interested"`: User is interested but not confirmed (future feature)
- `"maybe"`: User might attend (future feature)

## Event Capacity Management

When events reach capacity:

```json
{
  "detail": "Event has reached maximum capacity",
  "error_code": "EVENT_FULL",
  "max_attendees": 50,
  "current_attendees": 50
}
```

## Error Responses

### Already RSVP'd

```json
{
  "detail": "You have already RSVP'd to this event",
  "error_code": "ALREADY_RSVPED"
}
```

### Not RSVP'd

```json
{
  "detail": "You have not RSVP'd to this event",
  "error_code": "NOT_RSVPED"
}
```

### Event Not Found

```json
{
  "detail": "Event not found",
  "error_code": "EVENT_NOT_FOUND"
}
```

### Event Cancelled

```json
{
  "detail": "Cannot RSVP to cancelled event",
  "error_code": "EVENT_CANCELLED"
}
```

### Past Event

```json
{
  "detail": "Cannot RSVP to past events",
  "error_code": "PAST_EVENT"
}
```

## Integration with Event Responses

When fetching events (authenticated users), each event includes:

```json
{
  "id": "event_123",
  "title": "Tech Meetup 2025",
  "current_attendees": 15,
  "max_attendees": 50,
  "rsvp_status": "going",
  "rsvp_date": "2025-06-28T10:00:00Z"
}
```

## Notifications (Future Feature)

RSVP actions will trigger notifications:

- Event creator gets notified of new RSVPs
- Users get reminders before events they RSVP'd to
- Updates when event details change

## Analytics (Future Feature)

RSVP data can be used for:

- Event popularity metrics
- User engagement tracking
- Recommendation algorithms
- Attendance prediction
