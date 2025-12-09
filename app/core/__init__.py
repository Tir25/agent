"""
Core Package

Central logic for the Sovereign Desktop:

- ToolRegistry: Central tool management and discovery
- Dispatcher: Routes intents to appropriate tools
- State: Application state management
"""

from .tool_registry import (
    ToolRegistry,
    registry,
    register_tool,
    get_tool,
    execute_tool,
    discover_tools,
)

__all__ = [
    "ToolRegistry",
    "registry",
    "register_tool",
    "get_tool", 
    "execute_tool",
    "discover_tools",
]
