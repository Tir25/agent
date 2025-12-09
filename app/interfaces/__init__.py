"""
Interfaces Package

Contains Abstract Base Classes (ABCs) that define contracts for all tools
and services. These interfaces ensure modularity and adherence to SOLID
principles, particularly:

- Interface Segregation Principle (ISP)
- Dependency Inversion Principle (DIP)

All concrete implementations in app/services/ must inherit from these interfaces.
"""

# New modular architecture
from .tool import BaseTool

# Legacy imports for backwards compatibility
from .tool_interface import BaseTool as LegacyBaseTool, ToolMetadata

__all__ = [
    "BaseTool",
    "LegacyBaseTool",
    "ToolMetadata",
]
