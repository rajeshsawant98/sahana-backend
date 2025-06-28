"""
Centralized error codes and messages for consistent error handling
"""
from enum import Enum
from typing import Dict, Any, Optional

class ErrorCode(Enum):
    # Authentication Errors
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    MISSING_TOKEN = "MISSING_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    
    # Resource Not Found Errors
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    FRIEND_REQUEST_NOT_FOUND = "FRIEND_REQUEST_NOT_FOUND"
    
    # Conflict Errors
    EVENT_FULL = "EVENT_FULL"
    ALREADY_RSVPED = "ALREADY_RSVPED"
    EMAIL_EXISTS = "EMAIL_EXISTS"
    ALREADY_FRIENDS = "ALREADY_FRIENDS"
    FRIEND_REQUEST_PENDING = "FRIEND_REQUEST_PENDING"
    
    # Validation Errors
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_DATE = "INVALID_DATE"
    INVALID_PAGINATION = "INVALID_PAGINATION"
    PAST_EVENT = "PAST_EVENT"
    EVENT_CANCELLED = "EVENT_CANCELLED"
    
    # Request Errors
    NOT_RSVPED = "NOT_RSVPED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    
    # Server Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"

class ErrorMessage:
    """Standard error messages"""
    
    # Authentication
    INVALID_TOKEN = "Invalid authentication credentials"
    TOKEN_EXPIRED = "Authentication token has expired"
    MISSING_TOKEN = "Authentication token is required"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions for this action"
    INVALID_CREDENTIALS = "Invalid email or password"
    
    # Resources
    EVENT_NOT_FOUND = "Event not found"
    USER_NOT_FOUND = "User not found"
    FRIEND_REQUEST_NOT_FOUND = "Friend request not found"
    
    # Conflicts
    EVENT_FULL = "Event has reached maximum capacity"
    ALREADY_RSVPED = "You have already RSVP'd to this event"
    EMAIL_EXISTS = "User with this email already exists"
    ALREADY_FRIENDS = "Users are already friends"
    FRIEND_REQUEST_PENDING = "Friend request already pending"
    
    # Validation
    INVALID_EMAIL = "Invalid email format"
    INVALID_DATE = "Invalid date format"
    INVALID_PAGINATION = "Invalid pagination parameters"
    PAST_EVENT = "Cannot perform action on past events"
    EVENT_CANCELLED = "Cannot perform action on cancelled event"
    
    # Requests
    NOT_RSVPED = "User has not RSVP'd to this event"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Try again later."
    FILE_TOO_LARGE = "Uploaded file exceeds size limit"
    INVALID_FILE_TYPE = "File type not allowed"
    
    # Server
    INTERNAL_ERROR = "An internal server error occurred"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    DATABASE_ERROR = "Database operation failed"

def create_error_response(
    error_code: ErrorCode, 
    message: Optional[str] = None, 
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        error_code: Error code enum
        message: Custom error message (uses default if None)
        details: Additional error details
    """
    response = {
        "error_code": error_code.value,
        "detail": message or getattr(ErrorMessage, error_code.name),
    }
    
    if details:
        response.update(details)
        
    return response

# HTTP Status Code mappings
ERROR_STATUS_CODES = {
    # 400 Bad Request
    ErrorCode.NOT_RSVPED: 400,
    ErrorCode.INVALID_PAGINATION: 400,
    ErrorCode.PAST_EVENT: 400,
    ErrorCode.EVENT_CANCELLED: 400,
    ErrorCode.FILE_TOO_LARGE: 400,
    ErrorCode.INVALID_FILE_TYPE: 400,
    ErrorCode.INVALID_EMAIL: 400,
    ErrorCode.INVALID_DATE: 400,
    
    # 401 Unauthorized
    ErrorCode.INVALID_TOKEN: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.MISSING_TOKEN: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    
    # 403 Forbidden
    ErrorCode.INSUFFICIENT_PERMISSIONS: 403,
    
    # 404 Not Found
    ErrorCode.EVENT_NOT_FOUND: 404,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.FRIEND_REQUEST_NOT_FOUND: 404,
    
    # 409 Conflict
    ErrorCode.EVENT_FULL: 409,
    ErrorCode.ALREADY_RSVPED: 409,
    ErrorCode.EMAIL_EXISTS: 409,
    ErrorCode.ALREADY_FRIENDS: 409,
    ErrorCode.FRIEND_REQUEST_PENDING: 409,
    
    # 429 Too Many Requests
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    
    # 500 Internal Server Error
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.DATABASE_ERROR: 500,
    
    # 503 Service Unavailable
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}

def get_status_code(error_code: ErrorCode) -> int:
    """Get HTTP status code for error"""
    return ERROR_STATUS_CODES.get(error_code, 500)
