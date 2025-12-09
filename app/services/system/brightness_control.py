"""
Brightness Control Tool - Display Management

Single-responsibility tool for display brightness control.
Dependencies: screen_brightness_control
"""

from app.interfaces import BaseTool
from app.utils import Result

# Lazy import to isolate dependencies
_sbc = None


def _init_sbc():
    """Initialize screen brightness control on first use."""
    global _sbc
    if _sbc is not None:
        return True
    try:
        import screen_brightness_control as sbc
        _sbc = sbc
        return True
    except ImportError:
        return False


class BrightnessControlTool(BaseTool):
    """Tool for controlling display brightness."""
    
    @property
    def name(self) -> str:
        return "set_brightness"
    
    @property
    def description(self) -> str:
        return "Sets the display brightness (0-100) or gets current brightness"
    
    def execute(self, params: dict) -> Result:
        """
        Execute brightness control.
        
        Params:
            level: Brightness level 0-100 (optional)
            display: Display index or name (optional)
            action: 'get' to get current brightness
        """
        if not _init_sbc():
            return Result.fail("Brightness control not available")
        
        action = params.get("action", "set")
        display = params.get("display")
        
        if action == "get":
            try:
                level = _sbc.get_brightness(display=display)
                if isinstance(level, list):
                    level = level[0] if level else None
                return Result.ok({"brightness": level})
            except Exception as e:
                return Result.fail(f"Failed to get brightness: {e}")
        
        if "level" in params:
            level = max(0, min(100, int(params["level"])))
            try:
                _sbc.set_brightness(level, display=display)
                return Result.ok({"brightness": level})
            except Exception as e:
                return Result.fail(f"Failed to set brightness: {e}")
        
        return Result.fail("No action specified. Use level or action='get'")
