"""
Service layer decorators for common patterns like error handling and logging
"""
import functools
import logging
from typing import Any, Callable, Optional, Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_service_errors(
    default_return: Any = None,
    error_message_prefix: Optional[str] = None,
    reraise: bool = False
):
    """
    Decorator to handle service layer exceptions consistently
    
    Args:
        default_return: Default value to return on error
        error_message_prefix: Custom prefix for error messages
        reraise: Whether to reraise the exception after logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_name = func.__name__
                error_prefix = error_message_prefix or f"Error in {func_name}"
                error_msg = f"{error_prefix}: {str(e)}"
                
                # Log the error with context
                logger.error(error_msg, exc_info=True)
                
                if reraise:
                    raise e
                    
                return default_return
        return wrapper
    return decorator

def handle_friend_service_errors(func: Callable) -> Callable:
    """
    Specialized decorator for friend service methods that return dict responses
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            func_name = func.__name__
            error_msg = f"Error in {func_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False, 
                "error": str(e)
            }
    return wrapper

def handle_pagination_errors(func: Callable) -> Callable:
    """
    Decorator for paginated service methods
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            func_name = func.__name__
            error_msg = f"Error in {func_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Extract pagination params from arguments
            pagination = None
            for arg in args:
                if hasattr(arg, 'page') and hasattr(arg, 'page_size'):
                    pagination = arg
                    break
            
            if pagination:
                # Import here to avoid circular imports
                from app.models.pagination import EventPaginatedResponse
                return EventPaginatedResponse.create([], 0, pagination.page, pagination.page_size)
            else:
                return []
    return wrapper

# Convenience decorators for common return types
def handle_list_errors(func: Callable) -> Callable:
    """Returns empty list on error"""
    return handle_service_errors(default_return=[])(func)

def handle_dict_errors(func: Callable) -> Callable:
    """Returns empty dict on error"""
    return handle_service_errors(default_return={})(func)

def handle_bool_errors(func: Callable) -> Callable:
    """Returns False on error"""
    return handle_service_errors(default_return=False)(func)

def handle_none_errors(func: Callable) -> Callable:
    """Returns None on error"""
    return handle_service_errors(default_return=None)(func)
