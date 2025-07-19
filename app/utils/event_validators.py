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
    def validate_user_not_rsvped(event: Dict[str, Any], email: str) -> None:
        """
        Validate that a user has not already RSVP'd to an event.
        
        Args:
            event: Event dictionary
            email: User email
            
        Raises:
            ValueError: If user has already RSVP'd
        """
        rsvp_list = event.get("rsvpList", [])
        if email in rsvp_list:
            raise ValueError("You have already RSVP'd to this event")
    
    @staticmethod
    def validate_user_has_rsvped(event: Dict[str, Any], email: str) -> None:
        """
        Validate that a user has RSVP'd to an event.
        
        Args:
            event: Event dictionary
            email: User email
            
        Raises:
            ValueError: If user has not RSVP'd
        """
        rsvp_list = event.get("rsvpList", [])
        if email not in rsvp_list:
            raise ValueError("You have not RSVP'd to this event")
    
    @staticmethod
    def validate_rsvp_preconditions(event: Dict[str, Any], email: str) -> None:
        """
        Validate all preconditions for RSVP action.
        
        Args:
            event: Event dictionary
            email: User email
            
        Raises:
            ValueError: If any validation fails
        """
        EventValidator.validate_not_archived(event)
        EventValidator.validate_user_not_rsvped(event, email)
    
    @staticmethod
    def validate_cancel_rsvp_preconditions(event: Dict[str, Any], email: str) -> None:
        """
        Validate all preconditions for cancelling RSVP.
        
        Args:
            event: Event dictionary
            email: User email
            
        Raises:
            ValueError: If any validation fails
        """
        EventValidator.validate_user_has_rsvped(event, email)
