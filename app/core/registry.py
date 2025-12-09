"""
Tool Registry - Central Tool Discovery and Management

This module provides a central registry for all tools in the system.
The "Brain" (Router) uses this registry to discover and execute tools
without knowing their internal implementation.

Usage:
    from app.core.registry import ToolRegistry
    from app.services.system.volume import VolumeTool
    
    # Create registry
    registry = ToolRegistry()
    
    # Register tools
    registry.register_tool(VolumeTool())
    
    # Get and execute a tool
    tool = registry.get_tool("set_volume")
    result = tool.execute(level=50)
    
    # List all tools (for LLM system prompt)
    prompt = registry.list_tools()
"""

from typing import Dict, List, Optional

from app.interfaces.tool import BaseTool
from app.utils.result import CommandResult


class ToolRegistry:
    """
    Central registry for tool discovery and management.
    
    The registry maintains a mapping of tool names to tool instances,
    allowing the Brain (Router) to find and execute tools dynamically
    without knowing their implementation details.
    
    Attributes:
        _tools: Internal dictionary mapping tool name to tool instance.
        
    Example:
        registry = ToolRegistry()
        registry.register_tool(VolumeTool())
        registry.register_tool(BrightnessTool())
        
        # Get tool by name
        tool = registry.get_tool("set_volume")
        result = tool.execute(level=75)
        
        # Get all tools for LLM prompt
        tools_prompt = registry.list_tools()
    """
    
    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool: A BaseTool instance to register.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
            
        Example:
            registry.register_tool(VolumeTool())
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Expected BaseTool instance, got {type(tool).__name__}")
        
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by its name.
        
        Args:
            name: The unique name of the tool.
            
        Returns:
            The tool instance if found, None otherwise.
            
        Example:
            tool = registry.get_tool("set_volume")
            if tool:
                result = tool.execute(level=50)
        """
        return self._tools.get(name)
    
    def list_tools(self) -> str:
        """
        Get a formatted string of all available tools and descriptions.
        
        This is designed to be included in the LLM System Prompt so the
        AI knows what tools are available and how to use them.
        
        Returns:
            Formatted string listing all tools with their descriptions.
            
        Example:
            >>> registry.list_tools()
            Available Tools:
            - set_volume: Sets the system volume (0-100)...
            - set_brightness: Sets the display brightness...
        """
        if not self._tools:
            return "No tools registered."
        
        lines = ["Available Tools:"]
        for name, tool in sorted(self._tools.items()):
            lines.append(f"  - {name}: {tool.description}")
        
        return "\n".join(lines)
    
    def get_tool_names(self) -> List[str]:
        """
        Get a list of all registered tool names.
        
        Returns:
            List of tool names.
        """
        return list(self._tools.keys())
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            List of all tool instances.
        """
        return list(self._tools.values())
    
    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"<ToolRegistry(tools={len(self._tools)})>"


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TOOL REGISTRY VERIFICATION")
    print("=" * 60)
    
    # Import tools
    from app.services.system.volume import VolumeTool
    from app.services.system.brightness import BrightnessTool
    from app.services.system.launcher import AppLauncherTool
    
    # Create registry
    registry = ToolRegistry()
    print(f"\n[1] Created registry: {registry}")
    
    # Register tools
    registry.register_tool(VolumeTool())
    registry.register_tool(BrightnessTool())
    registry.register_tool(AppLauncherTool())
    print(f"[2] Registered 3 tools: {registry}")
    
    # List tools (for LLM prompt)
    print(f"\n[3] Tools for LLM prompt:\n{registry.list_tools()}")
    
    # Get and execute volume tool
    print("\n[4] Testing get_tool and execute:")
    volume_tool = registry.get_tool("set_volume")
    if volume_tool:
        result = volume_tool.execute(level=50)
        print(f"    set_volume(level=50) -> {result}")
    
    # Get current volume to verify
    result = registry.get_tool("set_volume").execute(action="get")
    print(f"    get_volume() -> {result}")
    
    # Test brightness
    brightness_tool = registry.get_tool("set_brightness")
    if brightness_tool:
        result = brightness_tool.execute(action="get")
        print(f"    get_brightness() -> {result}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)
