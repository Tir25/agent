"""
Tool Registry - Central Tool Management

A clean way to call tools without giant if/else blocks.
Provides automatic discovery, registration, and execution of tools.

Features:
- register_tool(): Manual tool registration
- get_tool(): Retrieve tool by name
- execute_tool(): Safe execution with Result
- discover_tools(): Auto-scan app/services/ for BaseTool classes

Usage:
    from app.core.tool_registry import registry
    
    # Auto-discover all tools
    registry.discover_tools()
    
    # Execute by name
    result = registry.execute_tool("set_volume", {"level": 50})
"""

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

from app.interfaces import BaseTool
from app.utils import Result

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for discovering and managing tools.
    
    Provides a clean interface for tool execution without
    if/else chains. Tools are looked up by name and executed
    with the safe Result pattern.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._discovered = False
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool instance.
        
        Args:
            tool: An instance of a BaseTool subclass
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Expected BaseTool, got {type(tool)}")
        
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class (instantiates it).
        
        Args:
            tool_class: A BaseTool subclass
        """
        try:
            tool = tool_class()
            self.register_tool(tool)
        except Exception as e:
            logger.error(f"Failed to instantiate {tool_class.__name__}: {e}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name (e.g., "set_volume")
            
        Returns:
            BaseTool instance or None if not found
        """
        return self._tools.get(name)
    
    def execute_tool(self, name: str, params: dict = None) -> Result:
        """
        Execute a tool by name with safe error handling.
        
        This method never crashes - errors are returned in Result.
        
        Args:
            name: Tool name to execute
            params: Parameters to pass to the tool
            
        Returns:
            Result object with success/failure
        """
        params = params or {}
        
        tool = self.get_tool(name)
        if tool is None:
            return Result.fail(
                error=f"Tool not found: {name}",
                code="TOOL_NOT_FOUND",
                available_tools=list(self._tools.keys())
            )
        
        # Use the safe run() method
        return tool.run(params)
    
    def list_tools(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())
    
    def list_all(self) -> List[BaseTool]:
        """Get all registered tool instances."""
        return list(self._tools.values())
    
    def get_tool_info(self) -> List[dict]:
        """Get info about all tools for LLM context."""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]
    
    def discover_tools(self, package_path: str = "app.services") -> int:
        """
        Auto-discover and register all BaseTool classes.
        
        Scans the specified package recursively for any class
        that inherits from BaseTool and registers it.
        
        Args:
            package_path: Python package path to scan
            
        Returns:
            Number of tools discovered
        """
        if self._discovered:
            return len(self._tools)
        
        count = 0
        
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent
            
            # Walk through all submodules
            for importer, module_name, is_pkg in pkgutil.walk_packages(
                path=[str(package_dir)],
                prefix=f"{package_path}.",
            ):
                try:
                    module = importlib.import_module(module_name)
                    
                    # Find all BaseTool subclasses
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseTool) 
                            and obj is not BaseTool
                            and not inspect.isabstract(obj)):
                            try:
                                self.register_class(obj)
                                count += 1
                            except Exception as e:
                                logger.error(f"Failed to register {name}: {e}")
                                
                except Exception as e:
                    logger.debug(f"Could not import {module_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Discovery failed for {package_path}: {e}")
        
        self._discovered = True
        logger.info(f"Discovered {count} tools from {package_path}")
        return count
    
    def clear(self) -> None:
        """Clear all registered tools (for testing)."""
        self._tools.clear()
        self._discovered = False
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
    
    def __repr__(self) -> str:
        return f"<ToolRegistry({len(self._tools)} tools)>"


# Global registry instance
registry = ToolRegistry()


# Convenience functions
def register_tool(tool: BaseTool) -> None:
    """Register a tool to the global registry."""
    registry.register_tool(tool)


def get_tool(name: str) -> Optional[BaseTool]:
    """Get a tool from the global registry."""
    return registry.get_tool(name)


def execute_tool(name: str, params: dict = None) -> Result:
    """Execute a tool from the global registry."""
    return registry.execute_tool(name, params)


def discover_tools() -> int:
    """Discover and register all tools."""
    return registry.discover_tools()
