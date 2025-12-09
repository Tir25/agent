"""
Tool Interface - Abstract Base Class for All Tools

This module defines the contract that ALL tools in the Sovereign Desktop
must implement. By enforcing this interface, we ensure:

1. Consistent API across all tools
2. Easy tool discovery and registration
3. Uniform error handling via Result types
4. Self-documenting tool capabilities

Usage:
    from app.interfaces import BaseTool
    from app.utils import Result
    
    class MyTool(BaseTool):
        @property
        def name(self) -> str:
            return "my_tool"
        
        @property
        def description(self) -> str:
            return "Does something useful"
        
        def execute(self, params: dict) -> Result:
            # Implementation here
            return Result.ok(data={"done": True})
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar

# Import Result and safe execution
try:
    from app.utils.result import Result
    from app.utils.safe_execution import safe_execute, log_tool_error
    SAFE_EXECUTION_AVAILABLE = True
except ImportError:
    SAFE_EXECUTION_AVAILABLE = False
    # Fallback for when modules aren't created yet
    @dataclass
    class Result:
        success: bool
        data: Any = None
        error: Optional[str] = None
        
        @classmethod
        def ok(cls, data=None, **kw): return cls(True, data)
        
        @classmethod
        def fail(cls, error="", **kw): return cls(False, None, error)


@dataclass
class ToolMetadata:
    """
    Metadata describing a tool's capabilities and requirements.
    
    Used for tool discovery, validation, and documentation.
    """
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Sovereign Desktop"
    
    # Parameter schema for validation
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Required capabilities (e.g., "audio", "office", "browser")
    requires: List[str] = field(default_factory=list)
    
    # Tags for categorization
    tags: List[str] = field(default_factory=list)
    
    # Whether this tool has side effects
    has_side_effects: bool = True
    
    # Whether this tool is async
    is_async: bool = False


class BaseTool(ABC):
    """
    Abstract Base Class for all tools in the Sovereign Desktop.
    
    Every tool MUST inherit from this class and implement:
    - name (property): Unique identifier for the tool
    - description (property): Human-readable description  
    - execute(params): The main execution method
    
    Use run(params) instead of execute(params) for safe execution
    with automatic error isolation and logging.
    
    Example:
        class VolumeControlTool(BaseTool):
            @property
            def name(self) -> str:
                return "set_volume"
            
            @property
            def description(self) -> str:
                return "Sets the system volume to a specified level (0-100)"
            
            def execute(self, params: dict) -> Result:
                level = params.get("level", 50)
                # ... implementation
                return Result.ok(data={"volume": level})
        
        # Usage:
        tool = VolumeControlTool()
        result = tool.run({"level": 75})  # Safe execution - never crashes
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for this tool.
        
        Should be lowercase with underscores (snake_case).
        Examples: "set_volume", "open_app", "create_document"
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what this tool does.
        
        This is used for:
        - Tool discovery UI
        - LLM context when selecting tools
        - Documentation generation
        """
        pass
    
    @property
    def metadata(self) -> ToolMetadata:
        """
        Get full metadata for this tool.
        
        Override this to provide additional metadata like
        parameter schemas, tags, and requirements.
        """
        return ToolMetadata(
            name=self.name,
            description=self.description,
        )
    
    @abstractmethod
    def execute(self, params: dict) -> "Result":
        """
        Execute the tool with the given parameters.
        
        NOTE: Prefer using run(params) instead for safe execution.
        
        Args:
            params: Dictionary of parameters for the tool.
                    The expected keys depend on the specific tool.
                    
        Returns:
            Result object containing:
            - success: True if execution succeeded
            - data: Any output data from the tool
            - error: Error message if failed
            
        Raises:
            Should NOT raise exceptions. All errors should be
            captured and returned in the Result.error field.
        """
        pass
    
    def run(self, params: dict) -> "Result":
        """
        Safely execute the tool with error isolation.
        
        This is the RECOMMENDED way to run tools. It wraps execute()
        in error isolation so that:
        1. Exceptions are caught and logged to errors.log
        2. A user-friendly Result.fail() is returned instead of crashing
        3. The main agent loop continues running
        
        Args:
            params: Dictionary of parameters for the tool
            
        Returns:
            Result object - never raises exceptions
        """
        if SAFE_EXECUTION_AVAILABLE:
            return safe_execute(
                lambda: self.execute(params),
                tool_name=self.name
            )
        else:
            # Fallback without safe execution
            try:
                return self.execute(params)
            except Exception as e:
                return Result.fail(error=str(e))
    
    def validate_params(self, params: dict) -> "Result":
        """
        Validate parameters before execution.
        
        Override this to add custom validation logic.
        Called automatically by execute() if validation is enabled.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Result.ok() if valid, Result.fail() with error message if not
        """
        return Result(success=True)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


# Type variable for generic tool operations
T = TypeVar("T", bound=BaseTool)


class ToolRegistry:
    """
    Registry for discovering and managing tools.
    
    Provides a central place to register and look up tools by name.
    """
    
    _tools: Dict[str, BaseTool] = {}
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Register a tool instance."""
        cls._tools[tool.name] = tool
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_all(cls) -> List[BaseTool]:
        """Get all registered tools."""
        return list(cls._tools.values())
    
    @classmethod
    def list_names(cls) -> List[str]:
        """Get names of all registered tools."""
        return list(cls._tools.keys())
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (mainly for testing)."""
        cls._tools.clear()
