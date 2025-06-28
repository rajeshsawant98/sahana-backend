"""
Centralized logging configuration for the Sahana backend
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class SahanaFormatter(logging.Formatter):
    """Custom formatter for Sahana backend logs"""
    
    def format(self, record):
        # Add timestamp and level with colors for console
        if hasattr(record, 'pathname'):
            # Extract module name from path
            module = Path(record.pathname).stem
            record.module = module
        
        # Format the message
        return super().format(record)

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "app.log",
    console: bool = True
):
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (None to disable file logging)
        console: Whether to log to console
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Define format
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    formatter = SahanaFormatter(format_string)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
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
def log_request(logger: logging.Logger, method: str, path: str, user_id: Optional[str] = None):
    """Log incoming API requests"""
    user_info = f" (user: {user_id})" if user_id else ""
    logger.info(f"API Request: {method} {path}{user_info}")

def log_database_operation(logger: logging.Logger, operation: str, collection: str, doc_id: Optional[str] = None):
    """Log database operations"""
    doc_info = f" (doc: {doc_id})" if doc_id else ""
    logger.debug(f"DB Operation: {operation} on {collection}{doc_info}")

def log_service_call(logger: logging.Logger, service_method: str, args: Optional[dict] = None):
    """Log service method calls"""
    args_info = f" with args: {args}" if args else ""
    logger.debug(f"Service call: {service_method}{args_info}")

def log_error_with_context(logger: logging.Logger, error: Exception, context: dict):
    """Log errors with additional context"""
    logger.error(f"Error: {str(error)}", extra={"context": context}, exc_info=True)

# Initialize default logging on import (for development)
if __name__ != "__main__":
    setup_logging(level="INFO", console=True)
