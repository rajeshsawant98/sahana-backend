"""
HTTP Exception utilities to reduce code duplication in routes
"""
from fastapi import HTTPException
from typing import Optional


class HTTPExceptionHelper:
    """Helper class for creating consistent HTTP exceptions"""
    
    @staticmethod
    def not_found(resource: str = "Resource", detail: Optional[str] = None) -> HTTPException:
        """Create a 404 Not Found exception"""
        message = detail or f"{resource} not found"
        return HTTPException(status_code=404, detail=message)
    
    @staticmethod
    def server_error(operation: str = "Operation", detail: Optional[str] = None) -> HTTPException:
        """Create a 500 Internal Server Error exception"""
        message = detail or f"Failed to {operation.lower()}"
        return HTTPException(status_code=500, detail=message)
    
    @staticmethod
    def bad_request(message: str = "Invalid request") -> HTTPException:
        """Create a 400 Bad Request exception"""
        return HTTPException(status_code=400, detail=message)
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> HTTPException:
        """Create a 403 Forbidden exception"""
        return HTTPException(status_code=403, detail=message)
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> HTTPException:
        """Create a 401 Unauthorized exception"""
        return HTTPException(status_code=401, detail=message)
    
    @staticmethod
    def conflict(message: str = "Resource conflict") -> HTTPException:
        """Create a 409 Conflict exception"""
        return HTTPException(status_code=409, detail=message)


# Convenience functions for common cases
def event_not_found() -> HTTPException:
    """Standard event not found exception"""
    return HTTPExceptionHelper.not_found("Event")

def user_not_found() -> HTTPException:
    """Standard user not found exception"""
    return HTTPExceptionHelper.not_found("User")

def operation_failed(operation: str, error: Optional[Exception] = None) -> HTTPException:
    """Standard operation failed exception with optional error details"""
    detail = f"Failed to {operation}"
    if error:
        detail += f": {str(error)}"
    return HTTPExceptionHelper.server_error(detail=detail)
