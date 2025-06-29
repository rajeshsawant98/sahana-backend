# Event Repository Architecture

This document describes the refactored event repository architecture that follows the Single Responsibility Principle and provides better separation of concerns.

## Overview

The monolithic `EventRepository` has been split into several specialized repositories, each handling a specific domain of event-related operations. These repositories are managed through a facade pattern using `EventRepositoryManager`.

## Repository Structure

### 1. BaseRepository

**File:** `app/repositories/base_repository.py`

The base class that provides common functionality for all repositories:

- Database connection management
- Modular query filter methods
- Common CRUD operations
- Pagination and sorting utilities

**Key Methods:**

- `_apply_base_filters()` - Non-archived event filtering
- `_apply_location_filters()` - City/state filtering
- `_apply_user_filters()` - User-related filtering (creator, organizer, moderator, RSVP)
- `_apply_event_filters()` - Event-specific filtering
- `_apply_origin_filter()` - Source filtering (manual, scraped, etc.)
- `_apply_archived_filter()` - Archive status filtering
- `_apply_sorting()` - Query sorting
- `_apply_pagination()` - Query pagination
- `_get_total_count()` - Count for pagination metadata

### 2. EventCrudRepository

**File:** `app/repositories/event_crud_repository.py`

**Responsibility:** Basic CRUD operations on events

**Key Methods:**

- `create_event(data)` - Create a new event
- `get_event_by_id(event_id)` - Get event by ID
- `update_event(event_id, update_data)` - Update event
- `delete_event(event_id)` - Delete event

### 3. EventQueryRepository

**File:** `app/repositories/event_query_repository.py`

**Responsibility:** Complex queries and filtering operations

**Key Methods:**

- `get_all_events()` - Get all non-archived events
- `get_all_events_paginated(pagination, filters)` - Paginated events with filtering
- `get_nearby_events(city, state)` - Location-based events
- `get_nearby_events_paginated(city, state, pagination)` - Paginated location-based events
- `get_external_events(city, state)` - External/scraped events
- `get_external_events_paginated(city, state, pagination)` - Paginated external events
- `get_events_for_archiving()` - Events ready for archiving
- `delete_events_before_today()` - Cleanup old events

### 4. EventArchiveRepository

**File:** `app/repositories/event_archive_repository.py`

**Responsibility:** Event archiving and archive management

**Key Methods:**

- `archive_event(event_id, archived_by, reason)` - Archive single event
- `unarchive_event(event_id)` - Restore archived event
- `archive_events_by_ids(event_ids, archived_by, reason)` - Bulk archive
- `get_archived_events(user_email)` - Get archived events
- `get_archived_events_paginated(pagination, user_email)` - Paginated archived events
- `get_archive_statistics()` - Archive statistics and metrics

### 5. EventRsvpRepository

**File:** `app/repositories/event_rsvp_repository.py`

**Responsibility:** RSVP-related operations

**Key Methods:**

- `rsvp_to_event(event_id, user_email)` - Add RSVP
- `cancel_rsvp(event_id, user_email)` - Remove RSVP
- `get_rsvp_list(event_id)` - Get event RSVP list
- `get_user_rsvps(user_email)` - Get user's RSVPs
- `get_user_rsvps_paginated(user_email, pagination)` - Paginated user RSVPs
- `get_rsvp_statistics(event_id)` - RSVP statistics

### 6. EventUserRepository

**File:** `app/repositories/event_user_repository.py`

**Responsibility:** User-specific event queries

**Key Methods:**

- `get_events_by_creator(email)` - Events created by user
- `get_events_by_creator_paginated(email, pagination)` - Paginated created events
- `get_events_organized_by_user(user_email)` - Events user organizes
- `get_events_organized_by_user_paginated(user_email, pagination)` - Paginated organized events
- `get_events_moderated_by_user(user_email)` - Events user moderates
- `get_events_moderated_by_user_paginated(user_email, pagination)` - Paginated moderated events
- `update_event_roles(event_id, field, emails)` - Update organizers/moderators
- `get_user_event_summary(user_email)` - User event statistics

### 7. EventRepositoryManager (Facade)

**File:** `app/repositories/event_repository_manager.py`

**Responsibility:** Provides a unified interface to all specialized repositories

This is the main class that services should use. It delegates operations to the appropriate specialized repository while maintaining a consistent API.

## Usage Examples

### In Service Layer

```python
from app.repositories.event_repository_manager import EventRepositoryManager

class EventService:
    def __init__(self):
        self.event_repo = EventRepositoryManager()
    
    def create_event(self, data):
        return self.event_repo.create_event(data)
    
    def get_paginated_events(self, pagination, filters):
        events, total = self.event_repo.get_all_events_paginated(pagination, filters)
        return self.format_paginated_response(events, total, pagination)
    
    def archive_old_events(self):
        events_to_archive = self.event_repo.get_events_for_archiving()
        # Business logic for determining which events to archive
        event_ids = [e['eventId'] for e in events_to_archive if self.should_archive(e)]
        return self.event_repo.archive_events_by_ids(event_ids, "system", "Auto-archived")
```

### Direct Repository Usage (if needed)

```python
from app.repositories.event_query_repository import EventQueryRepository
from app.repositories.event_rsvp_repository import EventRsvpRepository

# For specialized operations that don't need the full manager
query_repo = EventQueryRepository()
rsvp_repo = EventRsvpRepository()

# Get complex filtered results
events, total = query_repo.get_all_events_paginated(pagination, filters)

# Handle RSVP operations
success = rsvp_repo.rsvp_to_event(event_id, user_email)
```

## Benefits of This Architecture

1. **Single Responsibility Principle**: Each repository has a focused, single responsibility
2. **Maintainability**: Easier to understand, test, and modify individual components
3. **Testability**: Each repository can be unit tested independently
4. **Flexibility**: Can be easily extended with new specialized repositories
5. **Performance**: Optimized queries for specific use cases
6. **Code Reuse**: Modular filters and utilities shared via BaseRepository

## Migration Notes

- The original `EventRepository` is marked as deprecated
- All existing functionality is preserved through the manager pattern
- Services can migrate gradually by switching to `EventRepositoryManager`
- No breaking changes to the external API

## Future Enhancements

- Add caching layer to frequently accessed repositories
- Implement repository-specific connection pooling
- Add repository-level metrics and monitoring
- Consider splitting complex repositories further if they grow
