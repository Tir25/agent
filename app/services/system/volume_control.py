"""
Volume Control Tool - Audio Management

Single-responsibility tool for system audio control.
Dependencies: pycaw (Windows audio API)
"""

from app.interfaces import BaseTool
from app.utils import Result

# Lazy import pycaw to isolate dependencies
_audio_available = None
_speakers = None


def _init_audio():
    """Initialize audio on first use."""
    global _audio_available, _speakers
    if _audio_available is not None:
        return _audio_available
    try:
        from pycaw.pycaw import AudioUtilities
        _speakers = AudioUtilities.GetSpeakers()
        _audio_available = True
    except ImportError:
        _audio_available = False
    except Exception:
        _audio_available = False
    return _audio_available


def _get_volume_interface():
    """Get the volume interface."""
    if not _init_audio() or _speakers is None:
        return None
    try:
        return _speakers.EndpointVolume
    except Exception:
        return None


class VolumeControlTool(BaseTool):
    """Tool for controlling system audio volume."""
    
    @property
    def name(self) -> str:
        return "set_volume"
    
    @property
    def description(self) -> str:
        return "Sets the system volume (0-100) or mutes/unmutes audio"
    
    def execute(self, params: dict) -> Result:
        """
        Execute volume control.
        
        Params:
            level: Volume level 0-100 (optional)
            mute: True/False to mute/unmute (optional)
            action: 'get' to get current volume
        """
        vol = _get_volume_interface()
        if vol is None:
            return Result.fail("Audio control not available")
        
        action = params.get("action", "set")
        
        if action == "get":
            level = int(vol.GetMasterVolumeLevelScalar() * 100)
            muted = vol.GetMute()
            return Result.ok({"volume": level, "muted": bool(muted)})
        
        if "mute" in params:
            vol.SetMute(bool(params["mute"]), None)
            return Result.ok({"muted": bool(params["mute"])})
        
        if "level" in params:
            level = max(0, min(100, int(params["level"])))
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            return Result.ok({"volume": level})
        
        return Result.fail("No action specified. Use level, mute, or action='get'")
