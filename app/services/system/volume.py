"""
Volume Service - System Audio Control

Single-responsibility tool for system volume control using pycaw.
This service is fully isolated - if pycaw is missing, only this tool fails.

Dependencies:
    - pycaw: Windows Core Audio Python library
    - comtypes: Required by pycaw

Usage:
    from app.services.system.volume import VolumeTool
    
    tool = VolumeTool()
    result = tool.execute(level=75)  # Set volume to 75%
    result = tool.execute(action="get")  # Get current volume
    result = tool.execute(mute=True)  # Mute audio
"""

from typing import Any, Optional

from app.interfaces.tool import BaseTool
from app.utils.result import CommandResult


def _get_volume_interface() -> Any:
    """
    Get a fresh volume interface each time.
    
    This avoids caching issues where the interface becomes stale.
    
    Returns:
        Volume interface if available, None otherwise.
    """
    try:
        from pycaw.pycaw import AudioUtilities
        
        # Get default audio device speakers - fresh each time
        devices = AudioUtilities.GetSpeakers()
        return devices.EndpointVolume
        
    except ImportError:
        return None
    except Exception:
        return None


class VolumeTool(BaseTool):
    """
    Tool for controlling system audio volume.
    
    This tool uses pycaw (Python Core Audio Windows) to control
    the system master volume. It supports setting volume levels,
    muting/unmuting, and getting current volume.
    
    Example:
        tool = VolumeTool()
        
        # Set volume to 50%
        result = tool.execute(level=50)
        
        # Get current volume
        result = tool.execute(action="get")
        
        # Mute audio
        result = tool.execute(mute=True)
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for this tool."""
        return "set_volume"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Sets the system volume (0-100), mutes/unmutes audio, or gets current volume level"
    
    def _run(self, **kwargs: Any) -> CommandResult:
        """
        Execute volume control logic.
        
        Args:
            level: Volume level 0-100 (optional)
            mute: True/False to mute/unmute (optional)
            action: 'get' to retrieve current volume (optional)
            
        Returns:
            CommandResult with volume data or error.
        """
        # Get fresh volume interface each time
        volume = _get_volume_interface()
        
        if volume is None:
            return CommandResult(
                success=False,
                error="Audio control not available. Is pycaw installed?"
            )
        
        action = kwargs.get("action", "set")
        
        # Get current volume
        if action == "get":
            current_level = int(volume.GetMasterVolumeLevelScalar() * 100)
            is_muted = bool(volume.GetMute())
            return CommandResult(
                success=True,
                data={"volume": current_level, "muted": is_muted}
            )
        
        # Mute/unmute
        if "mute" in kwargs:
            mute_state = bool(kwargs["mute"])
            volume.SetMute(int(mute_state), None)
            return CommandResult(
                success=True,
                data={"muted": mute_state}
            )
        
        # Set volume level
        if "level" in kwargs:
            level = kwargs["level"]
            
            # Validate level
            if not isinstance(level, (int, float)):
                return CommandResult(
                    success=False,
                    error=f"Volume level must be a number, got {type(level).__name__}"
                )
            
            # Clamp to valid range
            level = max(0, min(100, int(level)))
            
            # Set volume (0.0 to 1.0 scale)
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            
            return CommandResult(
                success=True,
                data={"volume": level}
            )
        
        return CommandResult(
            success=False,
            error="No action specified. Use level=<0-100>, mute=<True/False>, or action='get'"
        )
