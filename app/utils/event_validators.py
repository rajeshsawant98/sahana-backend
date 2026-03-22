"""
Event validation utilities to reduce code duplication
"""
from typing import Dict, Optional, Any


class EventValidator:
    """Helper class for common event validation patterns"""
    
    @staticmethod
    def validate_event_exists(event: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that an event exists.
        
        Args:
            event: Event dictionary or None
            
        Returns:
            The event dictionary
            
        Raises:
            ValueError: If event is None
        """
        if not event:
            raise ValueError("Event not found")
        return event
    
    @staticmethod
    def validate_not_archived(event: Dict[str, Any]) -> None:
        """
        Validate that an event is not archived.
        
        Args:
            event: Event dictionary
            
        Raises:
            ValueError: If event is archived
        """
        if event.get("isArchived", False):
            raise ValueError("Cannot perform action on archived event")
    
    
    @staticmethod
    def validate_rsvp_preconditions(event: Dict[str, Any], email: str) -> None:
        """Validate preconditions for RSVP — duplicate check is handled by the DB upsert."""
        EventValidator.validate_not_archived(event)

    @staticmethod
    def validate_cancel_rsvp_preconditions(event: Dict[str, Any], email: str) -> None:
        """Validate preconditions for cancel RSVP — existence check is handled by DELETE rowcount."""
        EventValidator.validate_not_archived(event)
