# Event Archive/Soft Delete Documentation

## Overview

The Sahana backend now supports soft delete functionality for events through an archive system. This allows events to be "deleted" without permanently removing them from the database, providing better data integrity and the ability to restore events if needed.

## Key Features

### 🗃️ **Soft Delete (Archive)**

- Events are marked as archived instead of being permanently deleted
- Archived events are hidden from regular queries but remain in the database
- Archive metadata includes timestamp, user who archived, and reason

### 🔄 **Restore Capability**

- Archived events can be unarchived/restored
- All original event data is preserved during archiving

### ⏰ **Automatic Past Event Archiving**

- Bulk operation to archive all events that have ended
- Useful for cleaning up old events while preserving data

### 🔒 **Access Control**

- Only event creators can archive/unarchive their events
- Admins can perform bulk archive operations
- Archived events list is filtered by user permissions

## Database Schema Changes

### New Fields Added to Events

```javascript
{
  // Existing event fields...
  
  // Archive fields
  "isArchived": false,           // Boolean flag
  "archivedAt": null,           // ISO timestamp when archived
  "archivedBy": null,           // Email of user who archived
  "archiveReason": null         // Reason for archiving
}
```

## API Endpoints

### Archive an Event

```http
PATCH /events/{event_id}/archive
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Event completed successfully"
}
```

**Response:**

```json
{
  "message": "Event archived successfully",
  "archived_by": "user@example.com",
  "reason": "Event completed successfully"
}
```

### Unarchive an Event

```http
PATCH /events/{event_id}/unarchive
Authorization: Bearer <token>
```

**Response:**

```json
{
  "message": "Event restored successfully"
}
```

### Get My Archived Events

```http
GET /events/me/archived
Authorization: Bearer <token>
```

**Response:**

```json
{
  "archived_events": [
    {
      "eventId": "abc123",
      "eventName": "Past Tech Meetup",
      "isArchived": true,
      "archivedAt": "2025-06-28T10:00:00Z",
      "archivedBy": "creator@example.com",
      "archiveReason": "Event completed",
      // ... other event fields
    }
  ],
  "count": 1
}
```

### Bulk Archive Past Events (Admin Only)

```http
POST /events/archive/past-events
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "message": "Successfully archived 15 past events",
  "archived_count": 15,
  "archived_by": "admin@example.com"
}
```

## Service Methods

### Archive Event

```python
from app.services.event_service import archive_event

success = archive_event(
    event_id="abc123",
    archived_by="user@example.com", 
    reason="Event cancelled due to weather"
)
```

### Unarchive Event

```python
from app.services.event_service import unarchive_event

success = unarchive_event("abc123")
```

### Get Archived Events

```python
from app.services.event_service import get_archived_events

# Get all archived events by a specific user
archived_events = get_archived_events("user@example.com")

# Get all archived events (admin only)
all_archived = get_archived_events()
```

### Check if Event is Past

```python
from app.services.event_service import is_event_past, get_event_by_id

event = get_event_by_id("abc123")
if event and is_event_past(event):
    print("This event has ended")
```

### Bulk Archive Past Events

```python
from app.services.event_service import archive_past_events

# Archive all events that have ended
archived_count = archive_past_events("system")
print(f"Archived {archived_count} past events")
```

## Query Behavior Changes

### Filtered Queries

All regular event queries now automatically filter out archived events:

- `GET /events/` - Only returns non-archived events
- `GET /events/me/created` - Only returns non-archived events created by user
- `GET /events/me/rsvped` - Only returns non-archived events user RSVP'd to
- `GET /events/location/nearby` - Only returns non-archived nearby events

### Archive-Specific Queries

- `GET /events/me/archived` - Returns only archived events by user
- Archive queries are separate from regular queries

## Migration Strategy

### For Existing Events

Events created before the archive feature will have archive fields automatically initialized:

```javascript
{
  "isArchived": false,
  "archivedAt": null,
  "archivedBy": null,
  "archiveReason": null
}
```

### Backward Compatibility

- Existing API endpoints continue to work unchanged
- Old events without archive fields are treated as non-archived
- No breaking changes to existing functionality

## Use Cases

### 1. Event Completed

```python
# Mark a successfully completed event as archived
archive_event(event_id, creator_email, "Event completed successfully")
```

### 2. Event Cancelled

```python
# Archive a cancelled event
archive_event(event_id, creator_email, "Event cancelled due to low registration")
```

### 3. Cleanup Past Events

```python
# Periodically clean up old events (could be run as a cron job)
archived_count = archive_past_events("system")
```

### 4. Restore Accidentally Archived Event

```python
# Restore an event that was archived by mistake
unarchive_event(event_id)
```

## Error Handling

### Archive Non-Existent Event

```json
{
  "detail": "Event not found",
  "status_code": 404
}
```

### Archive Without Permission

```json
{
  "detail": "Only creator can access this",
  "status_code": 403
}
```

### Archive Already Archived Event

The system allows re-archiving with updated metadata.

## Best Practices

### 1. Provide Meaningful Reasons

```python
# Good
archive_event(event_id, user_email, "Event completed - 50 attendees")

# Not as helpful  
archive_event(event_id, user_email, "Done")
```

### 2. Archive Past Events Regularly

Set up a scheduled task to archive past events:

```python
# Weekly cleanup job
def weekly_cleanup():
    archived_count = archive_past_events("system")
    logger.info(f"Weekly cleanup: archived {archived_count} past events")
```

### 3. Check Event Status Before Actions

```python
event = get_event_by_id(event_id)
if event and event.get("isArchived"):
    return {"error": "Cannot modify archived event"}
```

## Demo Script

Run the demo script to see the archive functionality in action:

```bash
cd /path/to/sahana-backend
python demo_archive_events.py
```

The demo will:

1. Create test events (past and future)
2. Demonstrate archiving past events
3. Show how archived events are filtered from regular queries
4. Demonstrate unarchiving functionality
5. Show bulk archive of past events

## Performance Considerations

### Query Performance

- Archive filtering uses database indexes
- Minimal performance impact on regular queries
- Archive queries are separate and don't affect main performance

### Storage

- No additional storage overhead (just boolean + metadata fields)
- Archived events remain in same collection
- No separate archive database needed

## Future Enhancements

### Potential Features

- **Automatic Archive Rules**: Auto-archive events X days after they end
- **Archive Expiration**: Permanently delete events archived for > Y months  
- **Archive Categories**: Different archive types (completed, cancelled, postponed)
- **Bulk Restore**: Restore multiple archived events at once
- **Archive Audit Log**: Track all archive/unarchive operations
