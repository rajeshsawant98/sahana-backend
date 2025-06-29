"""
Event Repository Module

This module contains all event-related repository classes organized by functionality:
- CRUD operations
- Complex queries and filtering
- Archive management
- RSVP operations
- User-specific event queries
- Event ingestion
- Repository manager (facade)
"""

from .event_crud_repository import EventCrudRepository
from .event_query_repository import EventQueryRepository
from .event_archive_repository import EventArchiveRepository
from .event_rsvp_repository import EventRsvpRepository
from .event_user_repository import EventUserRepository
from .event_ingestion_repository import EventIngestionRepository
from .event_repository_manager import EventRepositoryManager

# For backward compatibility
from .event_repository_manager import EventRepositoryManager as EventRepository

__all__ = [
    'EventCrudRepository',
    'EventQueryRepository', 
    'EventArchiveRepository',
    'EventRsvpRepository',
    'EventUserRepository',
    'EventIngestionRepository',
    'EventRepositoryManager',
    'EventRepository',  # Backward compatibility alias
]
