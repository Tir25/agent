"""
Brightness Service - Display Brightness Control

Single-responsibility tool for display brightness control using screen_brightness_control.
This service is fully isolated - if screen_brightness_control is missing, only this tool fails.

Dependencies:
    - screen_brightness_control: Cross-platform brightness control library

Usage:
    from app.services.system.brightness import BrightnessTool
    
    tool = BrightnessTool()
    result = tool.execute(level=75)  # Set brightness to 75%
    result = tool.execute(action="get")  # Get current brightness
"""

from typing import Any, Optional

from app.interfaces.tool import BaseTool
from app.utils.result import CommandResult


def _get_sbc_module() -> Any:
    """
    Get the screen_brightness_control module.
    
    Returns fresh import each time to avoid caching issues.
    
    Returns:
        sbc module if available, None otherwise.
    """
    try:
        import screen_brightness_control as sbc
        return sbc
    except ImportError:
        return None
    except Exception:
        return None


class BrightnessTool(BaseTool):
    """
    Tool for controlling display brightness.
    
    This tool uses screen_brightness_control to manage display brightness
    levels. It supports setting brightness and getting current brightness.
    
    Example:
        tool = BrightnessTool()
        
        # Set brightness to 50%
        result = tool.execute(level=50)
        
        # Get current brightness  
        result = tool.execute(action="get")
        
        # Set brightness on specific display
        result = tool.execute(level=80, display=0)
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for this tool."""
        return "set_brightness"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Sets the display brightness (0-100) or gets current brightness level"
    
    def _run(self, **kwargs: Any) -> CommandResult:
        """
        Execute brightness control logic.
        
        Args:
            level: Brightness level 0-100 (optional)
            display: Display index or name (optional, defaults to primary)
            action: 'get' to retrieve current brightness (optional)
            
        Returns:
            CommandResult with brightness data or error.
        """
        # Get fresh module each time
        sbc = _get_sbc_module()
        
        if sbc is None:
            return CommandResult(
                success=False,
                error="Brightness control not available. Is screen_brightness_control installed?"
            )
        
        action = kwargs.get("action", "set")
        display = kwargs.get("display", None)
        
        # Get current brightness
        if action == "get":
            try:
                brightness = sbc.get_brightness(display=display)
                
                # Handle list return (multiple displays)
                if isinstance(brightness, list):
                    if len(brightness) == 1:
                        brightness = brightness[0]
                    else:
                        return CommandResult(
                            success=True,
                            data={"brightness": brightness, "displays": len(brightness)}
                        )
                
                return CommandResult(
                    success=True,
                    data={"brightness": brightness}
                )
                
            except Exception as e:
                return CommandResult(
                    success=False,
                    error=f"Failed to get brightness: {str(e)}"
                )
        
        # Set brightness level
        if "level" in kwargs:
            level = kwargs["level"]
            
            # Validate level
            if not isinstance(level, (int, float)):
                return CommandResult(
                    success=False,
                    error=f"Brightness level must be a number, got {type(level).__name__}"
                )
            
            # Clamp to valid range
            level = max(0, min(100, int(level)))
            
            try:
                sbc.set_brightness(level, display=display)
                
                return CommandResult(
                    success=True,
                    data={"brightness": level}
                )
                
            except Exception as e:
                return CommandResult(
                    success=False,
                    error=f"Failed to set brightness: {str(e)}"
                )
        
        return CommandResult(
            success=False,
            error="No action specified. Use level=<0-100> or action='get'"
        )
