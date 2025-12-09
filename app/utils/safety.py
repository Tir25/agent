"""
Safety Decorator - Error Isolation for Tool Execution

This module provides the @safe_execute decorator to prevent crashes in individual
tools from bringing down the entire agent.

Key Principle: If any tool crashes, the agent returns a graceful failure response
instead of crashing the terminal.

Usage:
    from app.utils.safety import safe_execute
    
    @safe_execute
    def risky_function(**kwargs):
        # If this crashes, it returns CommandResult(success=False) instead of raising
        return dangerous_operation()
"""

import functools
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, TypeVar

from .result import CommandResult

# Type variable for generic function return types
F = TypeVar("F", bound=Callable[..., Any])

# Configure logging for errors
_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    """
    Get or create the error logger that writes to app.log.
    
    This logger handles uncaught exceptions in tools and writes
    full tracebacks for debugging purposes.
    
    Returns:
        Configured logger instance.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("sovereign.safety")
        _logger.setLevel(logging.ERROR)
        
        # Prevent propagation to root logger
        _logger.propagate = False
        
        # Remove existing handlers to avoid duplicates
        _logger.handlers.clear()
        
        # Create file handler for app.log
        try:
            # Project root is 3 levels up: app/utils/safety.py -> app/utils -> app -> project root
            project_root = Path(__file__).parent.parent.parent
            log_path = project_root / "app.log"
        except Exception:
            log_path = Path("app.log")
        
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.ERROR)
        
        # Detailed format for error logs
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s\n"
            "%(message)s\n"
            + "-" * 60 + "\n"
        )
        file_handler.setFormatter(formatter)
        
        _logger.addHandler(file_handler)
    
    return _logger


def safe_execute(func: F) -> F:
    """
    Decorator that wraps function execution in error isolation.
    
    If the decorated function raises an exception:
    1. The error is logged with full traceback to app.log
    2. A CommandResult(success=False, error=str(e)) is returned
    3. The exception is NOT raised to the caller
    
    This ensures no tool ever crashes the main app.
    
    Args:
        func: The function to wrap.
        
    Returns:
        Decorated function that never raises exceptions.
        
    Example:
        @safe_execute
        def risky_operation(**kwargs) -> CommandResult:
            result = do_something_dangerous()
            return CommandResult(success=True, data=result)
        
        # Even if do_something_dangerous() raises, this won't crash:
        result = risky_operation(param="value")
        if result.success:
            print(result.data)
        else:
            print(f"Error: {result.error}")
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> CommandResult:
        try:
            result = func(*args, **kwargs)
            
            # If already a CommandResult, return as-is
            if isinstance(result, CommandResult):
                return result
            
            # Otherwise wrap the return value
            return CommandResult(success=True, data=result)
            
        except Exception as e:
            # Get full traceback
            tb = traceback.format_exc()
            
            # Log the error
            logger = _get_logger()
            error_message = (
                f"Function Error: {func.__name__}\n"
                f"Error Type: {type(e).__name__}\n"
                f"Error Message: {str(e)}\n"
                f"Traceback:\n{tb}"
            )
            logger.error(error_message)
            
            # Return a safe result - never crash
            return CommandResult(success=False, error=str(e))
    
    return wrapper  # type: ignore
