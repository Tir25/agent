"""
Result Object - CommandResult for Graceful Error Handling

This module provides the CommandResult dataclass that replaces raw return values,
allowing errors to propagate up the stack gracefully without exceptions.

The Result pattern ensures:
- No tool ever crashes the main application
- Explicit success/failure handling
- Easy logging via to_dict()

Usage:
    from app.utils.result import CommandResult
    
    def some_operation() -> CommandResult:
        try:
            data = do_something()
            return CommandResult(success=True, data=data)
        except Exception as e:
            return CommandResult(success=False, error=str(e))
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

# Type variables for generic operations
T = TypeVar("T")  # Success type
U = TypeVar("U")  # Transformation result type


@dataclass
class CommandResult:
    """
    A generic result container for operations that may fail.
    
    This ensures no tool ever crashes the main application by providing
    a structured way to return success/failure states.
    
    Attributes:
        success: True if the operation succeeded, False otherwise.
        data: The result data if successful (defaults to None).
        error: Error message if failed (defaults to None).
        
    Example:
        >>> result = CommandResult(success=True, data={"volume": 50})
        >>> result.to_dict()
        {'success': True, 'data': {'volume': 50}, 'error': None}
        
        >>> error_result = CommandResult(success=False, error="File not found")
        >>> error_result.to_dict()
        {'success': False, 'data': None, 'error': 'File not found'}
    """
    
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary for easy logging.
        
        Returns:
            Dictionary with success, data, and error fields.
        """
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }
    
    def __bool__(self) -> bool:
        """Allow using CommandResult in boolean context."""
        return self.success
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        if self.success:
            return f"CommandResult(success=True, data={self.data!r})"
        return f"CommandResult(success=False, error={self.error!r})"


# =============================================================================
# LEGACY SUPPORT - Result class for backwards compatibility
# =============================================================================

@dataclass
class Result(Generic[T]):
    """
    A generic Result container for operations that may fail.
    
    NOTE: This is the LEGACY Result class provided for backwards compatibility.
    For new code, prefer using CommandResult.
    
    Attributes:
        success: True if the operation succeeded, False otherwise
        data: The result data if successful (type T)
        error: Error message if failed
        error_code: Optional error code for programmatic handling
        metadata: Optional additional context about the result
    """
    
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def ok(cls, data: T = None, **metadata) -> "Result[T]":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def fail(cls, error: str, code: Optional[str] = None, **metadata) -> "Result[T]":
        """Create a failed result."""
        return cls(success=False, error=error, error_code=code, metadata=metadata)
    
    def __bool__(self) -> bool:
        """Allow using Result in boolean context."""
        return self.success
    
    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self.success
    
    def is_err(self) -> bool:
        """Check if result is an error."""
        return not self.success
    
    def unwrap(self) -> T:
        """Get the data, raising ValueError if failed."""
        if not self.success:
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        return self.data
    
    def unwrap_or(self, default: T) -> T:
        """Get the data or return a default value."""
        return self.data if self.success else default
    
    def unwrap_or_else(self, fn: Callable[[], T]) -> T:
        """Get the data or compute a default value."""
        return self.data if self.success else fn()
    
    def map(self, fn: Callable[[T], U]) -> "Result[U]":
        """Transform the success value."""
        if self.success:
            try:
                return Result.ok(fn(self.data), **self.metadata)
            except Exception as e:
                return Result.fail(str(e))
        return Result.fail(self.error, self.error_code, **self.metadata)
    
    def map_err(self, fn: Callable[[str], str]) -> "Result[T]":
        """Transform the error message."""
        if not self.success:
            return Result.fail(fn(self.error), self.error_code, **self.metadata)
        return self
    
    def and_then(self, fn: Callable[[T], "Result[U]"]) -> "Result[U]":
        """Chain another operation that returns a Result."""
        if self.success:
            try:
                return fn(self.data)
            except Exception as e:
                return Result.fail(str(e))
        return Result.fail(self.error, self.error_code, **self.metadata)
    
    def or_else(self, fn: Callable[[str], "Result[T]"]) -> "Result[T]":
        """Try an alternative operation if this one failed."""
        if not self.success:
            return fn(self.error)
        return self
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Result":
        """Create Result from dictionary."""
        return cls(
            success=d.get("success", False),
            data=d.get("data"),
            error=d.get("error"),
            error_code=d.get("error_code"),
            metadata=d.get("metadata", {}),
        )
    
    def __repr__(self) -> str:
        if self.success:
            return f"Result.ok({self.data!r})"
        return f"Result.fail({self.error!r})"


# Convenience aliases for more expressive code
def Ok(data: T = None, **metadata) -> Result[T]:
    """Shorthand for Result.ok()"""
    return Result.ok(data, **metadata)


def Err(error: str, code: Optional[str] = None, **metadata) -> Result:
    """Shorthand for Result.fail()"""
    return Result.fail(error, code, **metadata)


# Type aliases for common patterns
ResultBool = Result[bool]
ResultStr = Result[str]
ResultDict = Result[dict]
ResultList = Result[list]
