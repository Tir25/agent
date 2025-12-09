"""
Safe Execution - Error Isolation for Tool Execution

This module provides error isolation to prevent crashes in individual
tools from bringing down the entire agent. The "Ripple Effect" prevention.

Key Principle: If pywin32 crashes because Word isn't open, the Agent
simply says "I failed to access Word" rather than closing the terminal.

Usage:
    from app.utils.safe_execution import safe_tool_execution
    
    @safe_tool_execution
    def risky_function(params):
        # If this crashes, it returns Result.fail() instead of raising
        return dangerous_operation()
"""

import functools
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

from .result import Result

# Type variable for generic function return types
F = TypeVar("F", bound=Callable[..., Any])

# Configure error logging
_error_logger: Optional[logging.Logger] = None
_error_log_path: Optional[Path] = None


def _get_error_logger() -> logging.Logger:
    """
    Get or create the error logger that writes to errors.log.
    
    This logger is separate from the main application logger and
    specifically handles uncaught exceptions in tools.
    """
    global _error_logger, _error_log_path
    
    if _error_logger is None:
        _error_logger = logging.getLogger("sovereign.safe_execution")
        _error_logger.setLevel(logging.ERROR)
        
        # Prevent propagation to root logger
        _error_logger.propagate = False
        
        # Remove existing handlers
        _error_logger.handlers.clear()
        
        # Create file handler for errors.log
        try:
            # Try to find project root
            current = Path(__file__).parent.parent.parent  # app/utils -> app -> project root
            _error_log_path = current / "errors.log"
        except Exception:
            _error_log_path = Path("errors.log")
        
        file_handler = logging.FileHandler(_error_log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.ERROR)
        
        # Detailed format for error logs
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s\n"
            "%(message)s\n"
            "-" * 60 + "\n"
        )
        file_handler.setFormatter(formatter)
        
        _error_logger.addHandler(file_handler)
    
    return _error_logger


def log_tool_error(
    tool_name: str,
    error: Exception,
    params: Optional[dict] = None,
    extra_context: Optional[dict] = None
) -> None:
    """
    Log a tool error with full traceback to errors.log.
    
    Args:
        tool_name: Name of the tool that failed
        error: The exception that occurred
        params: Parameters passed to the tool (sensitive data redacted)
        extra_context: Additional context to log
    """
    logger = _get_error_logger()
    
    # Get the full traceback
    tb = traceback.format_exc()
    
    # Redact potentially sensitive data from params
    safe_params = _redact_sensitive_data(params) if params else {}
    
    # Build error message
    message = (
        f"Tool Error: {tool_name}\n"
        f"Error Type: {type(error).__name__}\n"
        f"Error Message: {str(error)}\n"
        f"Parameters: {safe_params}\n"
    )
    
    if extra_context:
        message += f"Context: {extra_context}\n"
    
    message += f"Traceback:\n{tb}"
    
    logger.error(message)


def _redact_sensitive_data(data: Any, keys_to_redact: set = None) -> Any:
    """
    Redact sensitive data from logs.
    
    Keys containing these words are redacted:
    password, secret, token, key, auth, credential
    """
    if keys_to_redact is None:
        keys_to_redact = {"password", "secret", "token", "key", "auth", "credential", "api_key"}
    
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(sensitive in k_lower for sensitive in keys_to_redact):
                result[k] = "[REDACTED]"
            else:
                result[k] = _redact_sensitive_data(v, keys_to_redact)
        return result
    elif isinstance(data, list):
        return [_redact_sensitive_data(item, keys_to_redact) for item in data]
    else:
        return data


def _generate_user_friendly_error(error: Exception) -> str:
    """
    Generate a user-friendly error message from an exception.
    
    This translates technical errors into more understandable messages.
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Common error translations
    translations = {
        "FileNotFoundError": "The file could not be found",
        "PermissionError": "Permission denied - the file may be in use",
        "ConnectionError": "Could not connect to the service",
        "TimeoutError": "The operation timed out",
        "AttributeError": "An internal error occurred",
        "pywintypes.com_error": "Failed to communicate with the application",
        "ModuleNotFoundError": "A required component is not installed",
    }
    
    # Check for COM errors (common with Office automation)
    if "com_error" in error_type.lower() or "pywintypes" in str(type(error)):
        return "Failed to communicate with the Windows application. It may not be installed or accessible."
    
    # Check translations
    for err_type, friendly_msg in translations.items():
        if err_type in error_type:
            return f"{friendly_msg}: {error_msg[:100]}"
    
    # Default: truncated error message
    if len(error_msg) > 150:
        error_msg = error_msg[:150] + "..."
    
    return f"Operation failed: {error_msg}"


def safe_tool_execution(
    func: F = None,
    *,
    tool_name: Optional[str] = None,
    reraise: bool = False,
    default_result: Any = None,
) -> Union[F, Callable[[F], F]]:
    """
    Decorator that wraps function execution in error isolation.
    
    If the decorated function raises an exception:
    1. The error is logged with full traceback to errors.log
    2. A user-friendly Result.fail() is returned
    3. The exception is NOT raised to the caller
    
    Args:
        func: The function to wrap (used when called without arguments)
        tool_name: Name to use in logs (defaults to function name)
        reraise: If True, re-raise after logging (for debugging)
        default_result: Value to include in Result.fail() data field
        
    Returns:
        Decorated function that never raises exceptions
        
    Example:
        @safe_tool_execution
        def risky_operation(params):
            return do_something_dangerous()
        
        @safe_tool_execution(tool_name="word_service")
        def create_document(params):
            return word.create(params["filename"])
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Result:
            name = tool_name or fn.__name__
            
            try:
                result = fn(*args, **kwargs)
                
                # If result is already a Result, return it
                if isinstance(result, Result):
                    return result
                
                # Otherwise wrap in Result.ok()
                return Result.ok(data=result)
                
            except Exception as e:
                # Log the error with full traceback
                params = {}
                if args:
                    # Try to extract params from first arg if it's a dict
                    if isinstance(args[0], dict):
                        params = args[0]
                    elif len(args) > 1 and isinstance(args[1], dict):
                        params = args[1]
                params.update(kwargs)
                
                log_tool_error(
                    tool_name=name,
                    error=e,
                    params=params,
                    extra_context={"function": fn.__qualname__}
                )
                
                # Generate user-friendly error message
                friendly_error = _generate_user_friendly_error(e)
                
                # Re-raise if requested (for debugging)
                if reraise:
                    raise
                
                # Return a safe Result
                return Result.fail(
                    error=friendly_error,
                    code=type(e).__name__,
                    tool=name,
                    original_error=str(e) if len(str(e)) < 200 else str(e)[:200],
                )
        
        return wrapper
    
    # Allow @safe_tool_execution or @safe_tool_execution()
    if func is not None:
        return decorator(func)
    return decorator


def safe_execute(fn: Callable, *args, tool_name: str = "unknown", **kwargs) -> Result:
    """
    Execute a function with error isolation (without decorator).
    
    Use this when you can't use the decorator, e.g., for lambdas
    or functions you don't control.
    
    Args:
        fn: Function to execute
        *args: Arguments to pass to function
        tool_name: Name for logging purposes
        **kwargs: Keyword arguments to pass to function
        
    Returns:
        Result with success or failure
        
    Example:
        result = safe_execute(
            lambda: word.create_document("test.docx"),
            tool_name="word_create"
        )
    """
    try:
        data = fn(*args, **kwargs)
        if isinstance(data, Result):
            return data
        return Result.ok(data=data)
    except Exception as e:
        log_tool_error(tool_name, e, kwargs)
        return Result.fail(
            error=_generate_user_friendly_error(e),
            code=type(e).__name__,
        )


class SafeExecutionContext:
    """
    Context manager for safe execution blocks.
    
    Use when you need to wrap a block of code rather than a function.
    
    Example:
        with SafeExecutionContext("word_operations") as ctx:
            doc = word.create()
            doc.write("Hello")
            ctx.result = doc.save()
        
        if ctx.success:
            print("Saved!")
        else:
            print(f"Error: {ctx.error}")
    """
    
    def __init__(self, name: str = "unknown", reraise: bool = False):
        self.name = name
        self.reraise = reraise
        self.success = True
        self.error: Optional[str] = None
        self.exception: Optional[Exception] = None
        self.result: Any = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.success = False
            self.exception = exc_val
            self.error = _generate_user_friendly_error(exc_val)
            
            log_tool_error(self.name, exc_val)
            
            if self.reraise:
                return False  # Re-raise the exception
            
            return True  # Suppress the exception
        
        return False
    
    def to_result(self) -> Result:
        """Convert context state to Result object."""
        if self.success:
            return Result.ok(data=self.result)
        return Result.fail(
            error=self.error,
            code=type(self.exception).__name__ if self.exception else "ERROR",
        )
