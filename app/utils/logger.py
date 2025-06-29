"""
Centralized logging configuration for the Sahana backend
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class SahanaLogFilter(logging.Filter):
    """Filter to add default values for custom log record attributes"""
    
    def filter(self, record):
        # Add default values for custom attributes if they don't exist
        if not hasattr(record, 'request_id'):
            record.req_id = ""
        else:
            record.req_id = f"[{getattr(record, 'request_id')}] "
            
        if not hasattr(record, 'user_email'):
            record.user_ctx = ""
        else:
            record.user_ctx = f"[user:{getattr(record, 'user_email')}] "
            
        return True

class SahanaFormatter(logging.Formatter):
    """Custom formatter for Sahana backend logs"""
    
    # Color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, *args, use_colors=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors
    
    def format(self, record):
        # Add timestamp and level with colors for console
        if hasattr(record, 'pathname'):
            # Extract module name from path
            module = Path(record.pathname).stem
            record.module = module
        
        # The filter already handles req_id and user_ctx, so we don't need to duplicate here
        
        # Format the message
        formatted = super().format(record)
        
        # Add colors for console output
        if self.use_colors and hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"
        
        return formatted

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "app.log",
    console: bool = True,
    use_colors: bool = True
):
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (None to disable file logging)
        console: Whether to log to console
        use_colors: Whether to use colors in console output
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create and add the custom filter
    sahana_filter = SahanaLogFilter()
    
    # Define format with more detailed information
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(req_id)s%(user_ctx)s%(module)s:%(lineno)d - %(message)s'
    
    # Console handler with colors
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = SahanaFormatter(format_string, use_colors=use_colors)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(sahana_filter)
        logger.addHandler(console_handler)
    
    # File handler without colors
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = SahanaFormatter(format_string, use_colors=False)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(sahana_filter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__)
    """
    return logging.getLogger(name)

# Service-specific loggers
def get_service_logger(service_name: str) -> logging.Logger:
    """Get logger for service layer"""
    return logging.getLogger(f"sahana.service.{service_name}")

def get_repository_logger(repo_name: str) -> logging.Logger:
    """Get logger for repository layer"""
    return logging.getLogger(f"sahana.repository.{repo_name}")

def get_route_logger(route_name: str) -> logging.Logger:
    """Get logger for route handlers"""
    return logging.getLogger(f"sahana.route.{route_name}")

# Log level utilities
def log_request(logger: logging.Logger, method: str, path: str, user_id: Optional[str] = None, request_id: Optional[str] = None):
    """Log incoming API requests with structured information"""
    extra = {}
    if user_id:
        extra['user_email'] = user_id
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"API Request: {method} {path}", extra=extra)

def log_database_operation(logger: logging.Logger, operation: str, collection: str, doc_id: Optional[str] = None, user_email: Optional[str] = None):
    """Log database operations with context"""
    extra = {}
    if user_email:
        extra['user_email'] = user_email
    
    doc_info = f" (doc: {doc_id})" if doc_id else ""
    logger.debug(f"DB Operation: {operation} on {collection}{doc_info}", extra=extra)

def log_service_call(logger: logging.Logger, service_method: str, args: Optional[dict] = None, user_email: Optional[str] = None):
    """Log service method calls with parameters"""
    extra = {}
    if user_email:
        extra['user_email'] = user_email
    
    # Sanitize sensitive data from args
    safe_args = {}
    if args:
        for key, value in args.items():
            if key.lower() in ['password', 'token', 'secret', 'credentials']:
                safe_args[key] = '***REDACTED***'
            else:
                safe_args[key] = value
    
    args_info = f" with args: {safe_args}" if safe_args else ""
    logger.debug(f"Service call: {service_method}{args_info}", extra=extra)

def log_error_with_context(logger: logging.Logger, error: Exception, context: dict, user_email: Optional[str] = None):
    """Log errors with additional context and user information"""
    extra = {}
    if user_email:
        extra['user_email'] = user_email
    
    # Add context to extra for structured logging
    extra.update(context)
    
    error_msg = f"Error: {str(error)}"
    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" | Context: {context_str}"
    
    logger.error(error_msg, extra=extra, exc_info=True)

def log_auth_event(logger: logging.Logger, event_type: str, user_email: Optional[str] = None, details: Optional[dict] = None):
    """Log authentication-related events"""
    extra = {}
    if user_email:
        extra['user_email'] = user_email
    
    detail_str = f" | Details: {details}" if details else ""
    logger.info(f"Auth Event: {event_type}{detail_str}", extra=extra)

def log_performance(logger: logging.Logger, operation: str, duration_ms: float, user_email: Optional[str] = None):
    """Log performance metrics"""
    extra = {}
    if user_email:
        extra['user_email'] = user_email
    
    logger.info(f"Performance: {operation} took {duration_ms:.2f}ms", extra=extra)

def log_jwt_payload(logger: logging.Logger, payload: dict, action: str = "JWT_DECODED"):
    """Log JWT payload information safely"""
    # Create a safe version of the payload for logging
    safe_payload = {
        'email': payload.get('data', {}).get('email', 'unknown'),
        'role': payload.get('data', {}).get('role', 'unknown'),
        'exp': payload.get('exp', 'unknown'),
        'action': action
    }
    
    extra = {'user_email': safe_payload['email']}
    logger.debug(f"JWT {action}: user={safe_payload['email']}, role={safe_payload['role']}, exp={safe_payload['exp']}", extra=extra)

# Initialize default logging on import (for development)
if __name__ != "__main__":
    setup_logging(level="INFO", console=True)
