"""
System Services Package

Single-responsibility tools for system control:
- volume: Audio control (NEW - uses _run pattern)
- brightness: Display brightness (NEW - uses _run pattern)
- launcher: App launching (NEW - uses _run pattern)
- screen_capture: Screenshot capture (NEW - uses _run pattern)

Legacy tools (backwards compatibility):
- volume_control: Legacy audio control
- brightness_control: Legacy display brightness
- process_manager: Legacy app launch/close
"""

# New modular architecture tools
from .volume import VolumeTool
from .brightness import BrightnessTool
from .launcher import AppLauncherTool
from .screen_capture import ScreenCaptureTool

# Legacy tools for backwards compatibility
from .volume_control import VolumeControlTool
from .brightness_control import BrightnessControlTool
from .process_manager import ProcessManagerTool

__all__ = [
    # New modular architecture
    "VolumeTool",
    "BrightnessTool",
    "AppLauncherTool",
    "ScreenCaptureTool",
    # Legacy (backwards compatibility)
    "VolumeControlTool",
    "BrightnessControlTool", 
    "ProcessManagerTool",
]

