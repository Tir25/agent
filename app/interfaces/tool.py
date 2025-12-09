"""
Tool Interface - Abstract Base Class for All Tools

This module defines the BaseTool contract that ALL tools in the Sovereign Desktop
must implement. By enforcing this interface, we ensure:

1. Consistent API across all tools
2. Easy tool discovery and registration
3. Uniform error handling via CommandResult
4. Self-documenting tool capabilities
5. Safe execution - no tool crashes the main app

Usage:
    from app.interfaces.tool import BaseTool
    from app.utils.result import CommandResult
    
    class MyTool(BaseTool):
        @property
        def name(self) -> str:
            return "my_tool"
        
        @property
        def description(self) -> str:
            return "Does something useful"
        
        def _run(self, **kwargs) -> CommandResult:
            # Implementation here
            return CommandResult(success=True, data={"done": True})
        
        # Use execute() for safe auto-wrapped execution
        result = my_tool.execute(param="value")
"""

from abc import ABC, abstractmethod
from typing import Any

from app.utils.result import CommandResult
from app.utils.safety import safe_execute


class BaseTool(ABC):
    """
    Abstract Base Class for all tools in the Sovereign Desktop.
    
    Every tool MUST inherit from this class and implement:
    - name (property): Unique identifier for the tool
    - description (property): Human-readable description  
    - _run(**kwargs): The actual tool logic implementation
    
    The execute(**kwargs) method wraps _run() with @safe_execute
    to ensure no tool ever crashes the main application.
    
    Example:
        class VolumeControlTool(BaseTool):
            @property
            def name(self) -> str:
                return "set_volume"
            
            @property
            def description(self) -> str:
                return "Sets the system volume to a specified level (0-100)"
            
            def _run(self, **kwargs) -> CommandResult:
                level = kwargs.get("level", 50)
                # ... actual implementation
                return CommandResult(success=True, data={"volume": level})
        
        # Usage:
        tool = VolumeControlTool()
        result = tool.execute(level=75)  # Safe execution - never crashes
        
        if result.success:
            print(f"Volume set to {result.data['volume']}")
        else:
            print(f"Error: {result.error}")
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for this tool.
        
        Should be lowercase with underscores (snake_case).
        Examples: "set_volume", "open_app", "create_document"
        
        Returns:
            The unique name of the tool.
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
        
        Returns:
            A clear description of the tool's purpose.
        """
        pass
    
    @abstractmethod
    def _run(self, **kwargs: Any) -> CommandResult:
        """
        Execute the actual tool logic.
        
        This method contains the core implementation of the tool.
        Override this method to implement your tool's functionality.
        
        NOTE: Do NOT call this method directly. Use execute() instead
        for safe execution with automatic error handling.
        
        Args:
            **kwargs: Keyword arguments for the tool.
                      The expected keys depend on the specific tool.
                      
        Returns:
            CommandResult object containing:
            - success: True if execution succeeded
            - data: Any output data from the tool
            - error: Error message if failed
        """
        pass
    
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Safely execute the tool with error isolation.
        
        This is the RECOMMENDED way to run tools. It wraps _run()
        with @safe_execute decorator so that:
        1. Exceptions are caught and logged to app.log
        2. A CommandResult(success=False) is returned instead of crashing
        3. The main agent loop continues running
        
        Args:
            **kwargs: Keyword arguments to pass to _run().
            
        Returns:
            CommandResult object - never raises exceptions.
        """
        @safe_execute
        def _execute_wrapper() -> CommandResult:
            return self._run(**kwargs)
        
        return _execute_wrapper()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<{self.__class__.__name__}(name='{self.name}')>"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.name}: {self.description}"
