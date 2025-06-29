"""
Repository Layer

This module provides data access layer for the Sahana backend application.
Repositories are organized by domain for better maintainability and separation of concerns.

Structure:
- events/     - Event-related repositories (CRUD, queries, archive, RSVP, etc.)
- users/      - User-related repositories  
- friends/    - Friend-related repositories
- base_repository.py - Common functionality shared across repositories

Usage:
    from app.repositories.events import EventRepositoryManager
    from app.repositories.users import UserRepository
    from app.repositories.friends import FriendRepository
"""

# Import base functionality
from .base_repository import BaseRepository

# Import domain-specific modules
from .events import (
    EventCrudRepository,
    EventQueryRepository,
    EventArchiveRepository, 
    EventRsvpRepository,
    EventUserRepository,
    EventIngestionRepository,
    EventRepositoryManager,
    EventRepository,  # Backward compatibility
)

from .users import UserRepository
from .friends import FriendRepository

__all__ = [
    # Base
    'BaseRepository',
    
    # Events
    'EventCrudRepository',
    'EventQueryRepository',
    'EventArchiveRepository',
    'EventRsvpRepository', 
    'EventUserRepository',
    'EventIngestionRepository',
    'EventRepositoryManager',
    'EventRepository',  # Backward compatibility
    
    # Users
    'UserRepository',
    
    # Friends
    'FriendRepository',
]
