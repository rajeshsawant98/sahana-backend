# Repository Organization

This document describes the organized structure of the repository layer in the Sahana backend.

## Directory Structure

```
app/repositories/
├── __init__.py                 # Main repository exports
├── base_repository.py          # Shared functionality and filters
│
├── events/                     # Event domain repositories
│   ├── __init__.py
│   ├── event_crud_repository.py      # Basic CRUD operations
│   ├── event_query_repository.py     # Complex queries and filtering
│   ├── event_archive_repository.py   # Archive operations
│   ├── event_rsvp_repository.py      # RSVP operations
│   ├── event_user_repository.py      # User-specific event queries
│   ├── event_ingestion_repository.py # External event ingestion
│   └── event_repository_manager.py   # Facade providing unified interface
│
├── users/                      # User domain repositories
│   ├── __init__.py
│   └── user_repository.py      # User management operations
│
└── friends/                    # Friend domain repositories
    ├── __init__.py
    └── friend_repository.py    # Friend management operations
```

## Import Patterns

### Recommended Imports (Domain-based)

```python
# Event repositories
from app.repositories.events import EventRepositoryManager
from app.repositories.events import EventCrudRepository  # If you need specific functionality

# User repositories  
from app.repositories.users import UserRepository

# Friend repositories
from app.repositories.friends import FriendRepository

# Base functionality
from app.repositories import BaseRepository
```

### Backward Compatibility

The main `__init__.py` file provides backward compatibility:

```python
# This still works for existing code
from app.repositories import EventRepositoryManager, UserRepository, FriendRepository
```

## Repository Responsibilities

### Events Domain (`events/`)

- **EventCrudRepository** - Create, read, update, delete operations
- **EventQueryRepository** - Complex filtering, search, and query operations
- **EventArchiveRepository** - Event archiving and archive management
- **EventRsvpRepository** - RSVP creation, cancellation, and listing
- **EventUserRepository** - User-specific event queries (my events, organized, moderated)
- **EventIngestionRepository** - External event data ingestion (Ticketmaster, etc.)
- **EventRepositoryManager** - Facade that combines all event repositories

### Users Domain (`users/`)

- **UserRepository** - User account management, authentication, profiles

### Friends Domain (`friends/`)

- **FriendRepository** - Friend relationships, requests, management

## Benefits of This Organization

✅ **Domain Separation** - Clear boundaries between different business domains
✅ **Single Responsibility** - Each repository has a focused purpose
✅ **Maintainability** - Easier to find and modify specific functionality
✅ **Team Collaboration** - Developers can work on different domains without conflicts
✅ **Testing** - Individual repositories can be unit tested independently
✅ **Scalability** - Easy to add new repositories or split existing ones
✅ **Clean Imports** - Clear, organized import statements

## Migration Notes

- All existing imports continue to work (backward compatibility maintained)
- No breaking changes to service layer or routes
- Deprecated monolithic `event_repository.py` has been removed
- All functionality preserved through the organized structure

## Usage Examples

```python
# Service layer usage
from app.repositories.events import EventRepositoryManager

class EventService:
    def __init__(self):
        self.event_repo = EventRepositoryManager()
    
    def create_event(self, event_data):
        return self.event_repo.create_event(event_data)
    
    def get_user_events(self, user_email):
        return self.event_repo.get_events_created_by_user(user_email)
```

```python
# Direct repository usage (if needed)
from app.repositories.events import EventCrudRepository, EventRsvpRepository

crud_repo = EventCrudRepository()
rsvp_repo = EventRsvpRepository()

# Use specific repositories for targeted operations
```

This organization follows domain-driven design principles and makes the codebase more maintainable and scalable.
