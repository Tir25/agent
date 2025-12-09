"""
Audio Control - System Audio and Media Management

Provides control over system audio including:
- Volume control
- Application-specific audio
- Media playback control
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    """Audio device information."""
    id: str
    name: str
    is_default: bool
    volume: float  # 0.0 to 1.0


@dataclass
class AudioSession:
    """Audio session for an application."""
    process_id: int
    name: str
    volume: float
    is_muted: bool


class AudioController:
    """
    System audio controller using pycaw.
    
    Provides comprehensive audio control for Windows including
    master volume, per-application volume, and media controls.
    """
    
    def __init__(self):
        """Initialize the audio controller."""
        self._init_audio()
        logger.info("Audio Controller initialized")
    
    def _init_audio(self):
        """Initialize audio interfaces."""
        try:
            from pycaw.pycaw import (
                AudioUtilities,
                IAudioEndpointVolume,
                ISimpleAudioVolume,
            )
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            
            self._AudioUtilities = AudioUtilities
            self._CLSCTX_ALL = CLSCTX_ALL
            self._POINTER = POINTER
            self._IAudioEndpointVolume = IAudioEndpointVolume
            self._cast = cast
            
            # Get master volume interface
            devices = self._AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                self._IAudioEndpointVolume._iid_, self._CLSCTX_ALL, None
            )
            self._master_volume = self._cast(interface, self._POINTER(self._IAudioEndpointVolume))
            
        except ImportError:
            raise ImportError("pycaw not installed. Run: pip install pycaw")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self._master_volume = None
    
    # ==================== Master Volume Control ====================
    
    def get_volume(self) -> float:
        """
        Get the current master volume level.
        
        Returns:
            Volume level from 0.0 to 1.0
        """
        if self._master_volume:
            return self._master_volume.GetMasterVolumeLevelScalar()
        return 0.0
    
    def set_volume(self, level: float):
        """
        Set the master volume level.
        
        Args:
            level: Volume level from 0.0 to 1.0
        """
        level = max(0.0, min(1.0, level))
        if self._master_volume:
            self._master_volume.SetMasterVolumeLevelScalar(level, None)
            logger.info(f"Volume set to {level * 100:.0f}%")
    
    def volume_up(self, amount: float = 0.1):
        """Increase volume by amount (default 10%)."""
        current = self.get_volume()
        self.set_volume(current + amount)
    
    def volume_down(self, amount: float = 0.1):
        """Decrease volume by amount (default 10%)."""
        current = self.get_volume()
        self.set_volume(current - amount)
    
    def is_muted(self) -> bool:
        """Check if master volume is muted."""
        if self._master_volume:
            return bool(self._master_volume.GetMute())
        return False
    
    def mute(self):
        """Mute master volume."""
        if self._master_volume:
            self._master_volume.SetMute(True, None)
            logger.info("Volume muted")
    
    def unmute(self):
        """Unmute master volume."""
        if self._master_volume:
            self._master_volume.SetMute(False, None)
            logger.info("Volume unmuted")
    
    def toggle_mute(self):
        """Toggle mute state."""
        if self.is_muted():
            self.unmute()
        else:
            self.mute()
    
    # ==================== Per-Application Volume ====================
    
    def get_audio_sessions(self) -> List[AudioSession]:
        """Get all active audio sessions (applications playing audio)."""
        sessions = []
        
        try:
            for session in self._AudioUtilities.GetAllSessions():
                if session.Process:
                    volume = session.SimpleAudioVolume
                    sessions.append(AudioSession(
                        process_id=session.Process.pid,
                        name=session.Process.name(),
                        volume=volume.GetMasterVolume(),
                        is_muted=bool(volume.GetMute()),
                    ))
        except Exception as e:
            logger.error(f"Failed to get audio sessions: {e}")
        
        return sessions
    
    def set_app_volume(self, process_name: str, level: float):
        """
        Set volume for a specific application.
        
        Args:
            process_name: Name of the process (e.g., "chrome.exe")
            level: Volume level from 0.0 to 1.0
        """
        level = max(0.0, min(1.0, level))
        
        try:
            for session in self._AudioUtilities.GetAllSessions():
                if session.Process and process_name.lower() in session.Process.name().lower():
                    session.SimpleAudioVolume.SetMasterVolume(level, None)
                    logger.info(f"Set {process_name} volume to {level * 100:.0f}%")
                    return True
        except Exception as e:
            logger.error(f"Failed to set app volume: {e}")
        
        return False
    
    def mute_app(self, process_name: str):
        """Mute a specific application."""
        try:
            for session in self._AudioUtilities.GetAllSessions():
                if session.Process and process_name.lower() in session.Process.name().lower():
                    session.SimpleAudioVolume.SetMute(True, None)
                    logger.info(f"Muted: {process_name}")
                    return True
        except Exception as e:
            logger.error(f"Failed to mute app: {e}")
        
        return False
    
    def unmute_app(self, process_name: str):
        """Unmute a specific application."""
        try:
            for session in self._AudioUtilities.GetAllSessions():
                if session.Process and process_name.lower() in session.Process.name().lower():
                    session.SimpleAudioVolume.SetMute(False, None)
                    logger.info(f"Unmuted: {process_name}")
                    return True
        except Exception as e:
            logger.error(f"Failed to unmute app: {e}")
        
        return False
    
    # ==================== Media Control ====================
    
    def media_play_pause(self):
        """Send play/pause media key."""
        self._send_media_key("play_pause")
    
    def media_next(self):
        """Send next track media key."""
        self._send_media_key("next_track")
    
    def media_previous(self):
        """Send previous track media key."""
        self._send_media_key("prev_track")
    
    def media_stop(self):
        """Send stop media key."""
        self._send_media_key("stop")
    
    def _send_media_key(self, key: str):
        """Send a media key using keyboard simulation."""
        try:
            import pyautogui
            
            key_map = {
                "play_pause": "playpause",
                "next_track": "nexttrack",
                "prev_track": "prevtrack",
                "stop": "stop",
                "volume_up": "volumeup",
                "volume_down": "volumedown",
                "volume_mute": "volumemute",
            }
            
            if key in key_map:
                pyautogui.press(key_map[key])
                logger.debug(f"Media key: {key}")
        except Exception as e:
            logger.error(f"Failed to send media key: {e}")
    
    # ==================== Audio Devices ====================
    
    def get_output_devices(self) -> List[AudioDevice]:
        """Get list of audio output devices."""
        devices = []
        
        try:
            for device in self._AudioUtilities.GetAllDevices():
                if device.state == 1:  # Active device
                    devices.append(AudioDevice(
                        id=device.id,
                        name=device.FriendlyName,
                        is_default=False,  # Would need more work to detect
                        volume=1.0,
                    ))
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
        
        return devices
