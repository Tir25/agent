"""
Utils Package

Shared utilities and helper classes for the Sovereign Desktop:

- CommandResult: Dataclass for graceful error handling (NEW)
- safe_execute: Decorator for error isolation (NEW) 
- Result: Legacy generic result type (backwards compatibility)
- safe_execution: Legacy error isolation (backwards compatibility)
"""

# New modular architecture
from .result import CommandResult
from .safety import safe_execute

# Legacy imports for backwards compatibility
from .result import Result, Ok, Err
from .safe_execution import (
    safe_tool_execution,
    safe_execute as legacy_safe_execute,
    SafeExecutionContext,
    log_tool_error,
)

__all__ = [
    # New modular architecture
    "CommandResult",
    "safe_execute",
    # Legacy (backwards compatibility)
    "Result",
    "Ok",
    "Err",
    "safe_tool_execution",
    "legacy_safe_execute",
    "SafeExecutionContext",
    "log_tool_error",
]
