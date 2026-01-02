"""
Error Handler Module for Mental Health Chatbot
Implements comprehensive error handling, logging, and monitoring
"""

import logging
import traceback
import sys
from datetime import datetime
from functools import wraps
from typing import Callable, Any, Optional
from logging.handlers import RotatingFileHandler
import os


# Create logs directory if it doesn't exist
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# Configure logging
def setup_logging():
    """Setup application logging with rotation"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation (max 10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'chatbot.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'errors.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


# Initialize logger
logger = setup_logging()


class ErrorHandler:
    """Central error handling class"""
    
    @staticmethod
    def handle_exception(error: Exception, context: str = "Unknown") -> dict:
        """Handle exception and return user-friendly error response"""
        error_type = type(error).__name__
        error_msg = str(error)
        stack_trace = traceback.format_exc()
        
        # Log the error
        logger.error(f"Error in {context}: {error_type} - {error_msg}")
        logger.debug(f"Stack trace:\n{stack_trace}")
        
        # Determine user message based on error type
        user_message = ErrorHandler._get_user_friendly_message(error_type, context)
        
        return {
            'error': True,
            'error_type': error_type,
            'message': user_message,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_user_friendly_message(error_type: str, context: str) -> str:
        """Convert technical error to user-friendly message"""
        
        error_messages = {
            'DatabaseError': "We're having trouble accessing your data. Please try again.",
            'ConnectionError': "Network connection issue. Please check your internet connection.",
            'TimeoutError': "The request took too long. Please try again.",
            'ValidationError': "Invalid input provided. Please check your data and try again.",
            'APIError': "AI service temporarily unavailable. Using fallback system.",
            'KeyError': "Missing required information. Please try again.",
            'ValueError': "Invalid data format. Please check your input.",
            'PermissionError': "Access denied. Please check your permissions.",
        }
        
        # Return specific message or generic fallback
        return error_messages.get(
            error_type,
            "An unexpected error occurred. Our team has been notified. Please try again."
        )
    
    @staticmethod
    def log_request(endpoint: str, user_id: int, data: Optional[dict] = None):
        """Log incoming request"""
        logger.info(f"Request to {endpoint} from user {user_id}")
        if data:
            logger.debug(f"Request data: {data}")
    
    @staticmethod
    def log_response(endpoint: str, user_id: int, status: str, duration: float):
        """Log response details"""
        logger.info(f"Response from {endpoint} for user {user_id}: {status} ({duration:.3f}s)")


def handle_errors(context: str = "Operation"):
    """
    Decorator for error handling
    
    Usage:
        @handle_errors("Chat endpoint")
        def chat_function():
            # your code here
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = ErrorHandler.handle_exception(e, context)
                return error_response
        return wrapper
    return decorator


def log_performance(func_name: str = None):
    """
    Decorator to log function performance
    
    Usage:
        @log_performance("LLM Query")
        def query_llm():
            # your code
    """
    def decorator(func: Callable) -> Callable:
        name = func_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"✓ {name} completed in {duration:.3f}s")
                return result
            
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"✗ {name} failed after {duration:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


class HealthMonitor:
    """Monitor application health"""
    
    def __init__(self):
        self.errors_count = 0
        self.warnings_count = 0
        self.last_error_time = None
        self.start_time = datetime.now()
    
    def record_error(self):
        """Record an error occurrence"""
        self.errors_count += 1
        self.last_error_time = datetime.now()
    
    def record_warning(self):
        """Record a warning"""
        self.warnings_count += 1
    
    def get_health_status(self) -> dict:
        """Get current health status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Determine health status
        if self.errors_count == 0:
            status = "Healthy"
        elif self.errors_count < 5:
            status = "Degraded"
        else:
            status = "Critical"
        
        return {
            'status': status,
            'uptime_seconds': round(uptime, 2),
            'total_errors': self.errors_count,
            'total_warnings': self.warnings_count,
            'last_error': self.last_error_time.isoformat() if self.last_error_time else None
        }
    
    def reset_counters(self):
        """Reset error and warning counters"""
        self.errors_count = 0
        self.warnings_count = 0


# Global health monitor instance
health_monitor = HealthMonitor()


def validate_input(data: dict, required_fields: list, field_types: dict = None) -> tuple:
    """
    Validate input data
    
    Args:
        data: Input data dictionary
        required_fields: List of required field names
        field_types: Optional dict mapping field names to expected types
    
    Returns:
        (is_valid, error_message) tuple
    """
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    # Check field types if provided
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False, f"Invalid type for {field}: expected {expected_type.__name__}"
    
    return True, None


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if denominator is zero"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure
    
    Usage:
        @retry_on_failure(max_retries=3, delay=2.0)
        def unreliable_function():
            # code that might fail
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            
            # All retries failed
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


# Export commonly used functions
__all__ = [
    'logger',
    'ErrorHandler',
    'handle_errors',
    'log_performance',
    'health_monitor',
    'validate_input',
    'safe_divide',
    'retry_on_failure'
]
