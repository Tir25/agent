"""
System Operations Module

Provides robust control over Windows hardware and applications:
- Audio Control: Volume management using Windows Core Audio API (pycaw)
- Display Control: Brightness management using DDC/CI (screen_brightness_control)
- Application Management: Launch, close, and focus applications (psutil, pygetwindow)

All functions include comprehensive error handling to prevent agent crashes.
"""

import logging
import subprocess
import time
import os
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Audio Controller
# ============================================================================

@dataclass
class AudioDevice:
    """Represents an audio endpoint device."""
    name: str
    id: str
    is_default: bool = False


class AudioController:
    """
    Controls Windows audio using the Core Audio API (pycaw).
    
    Provides control over master volume, mute state, and audio device enumeration.
    All operations are wrapped in try/except blocks to handle COM interface failures.
    
    Example:
        >>> audio = AudioController()
        >>> audio.set_master_volume(50)  # Set to 50%
        >>> audio.mute(True)  # Mute audio
        >>> print(audio.get_volume())  # Get current volume
    """
    
    def __init__(self):
        """
        Initialize the AudioController.
        
        Attempts to get the default audio endpoint for volume control.
        If audio system is unavailable, methods will fail gracefully.
        """
        self._volume_interface = None
        self._endpoint = None
        self._initialized = False
        
        try:
            from pycaw.pycaw import AudioUtilities
            
            # Get default audio endpoint (speakers)
            speakers = AudioUtilities.GetSpeakers()
            if speakers:
                # New pycaw API uses EndpointVolume property directly
                self._volume_interface = speakers.EndpointVolume
                self._endpoint = speakers
                self._initialized = True
                logger.info("AudioController initialized successfully")
            else:
                logger.warning("No audio devices found")
                
        except ImportError as e:
            logger.error(f"pycaw not installed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize AudioController: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if audio control is available."""
        return self._initialized and self._volume_interface is not None
    
    def get_volume(self) -> Optional[float]:
        """
        Get the current master volume level.
        
        Returns:
            Volume level as a percentage (0-100), or None if unavailable.
            
        Example:
            >>> audio = AudioController()
            >>> volume = audio.get_volume()
            >>> print(f"Current volume: {volume}%")
        """
        if not self.is_available:
            logger.warning("Audio control not available")
            return None
            
        try:
            # Get scalar volume (0.0 to 1.0) and convert to percentage
            volume = self._volume_interface.GetMasterVolumeLevelScalar()
            return round(volume * 100, 1)
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return None
    
    def set_master_volume(self, level_percent: Union[int, float]) -> bool:
        """
        Set the master volume level.
        
        Args:
            level_percent: Volume level as a percentage (0-100).
                           Values outside this range will be clamped.
                           
        Returns:
            True if successful, False otherwise.
            
        Example:
            >>> audio = AudioController()
            >>> audio.set_master_volume(75)  # Set to 75%
            True
            
        Note:
            This sets the scalar volume level. The actual dB level depends
            on the audio device's volume curve.
        """
        if not self.is_available:
            logger.warning("Audio control not available")
            return False
            
        try:
            # Clamp value to valid range
            level = max(0, min(100, float(level_percent)))
            scalar = level / 100.0
            
            # Set the volume (None for event context GUID)
            self._volume_interface.SetMasterVolumeLevelScalar(scalar, None)
            logger.info(f"Volume set to {level}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set volume to {level_percent}%: {e}")
            return False
    
    def mute_master_volume(self, mute: bool) -> bool:
        """
        Mute or unmute the master audio.
        
        Args:
            mute: True to mute, False to unmute.
            
        Returns:
            True if successful, False otherwise.
            
        Example:
            >>> audio = AudioController()
            >>> audio.mute_master_volume(True)   # Mute
            >>> audio.mute_master_volume(False)  # Unmute
        """
        if not self.is_available:
            logger.warning("Audio control not available")
            return False
            
        try:
            self._volume_interface.SetMute(1 if mute else 0, None)
            state = "muted" if mute else "unmuted"
            logger.info(f"Audio {state}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to {'mute' if mute else 'unmute'} audio: {e}")
            return False
    
    def is_muted(self) -> Optional[bool]:
        """
        Check if master audio is muted.
        
        Returns:
            True if muted, False if not muted, None if unavailable.
        """
        if not self.is_available:
            return None
            
        try:
            return bool(self._volume_interface.GetMute())
        except Exception as e:
            logger.error(f"Failed to get mute state: {e}")
            return None
    
    def toggle_mute(self) -> bool:
        """
        Toggle the mute state.
        
        Returns:
            True if successful, False otherwise.
        """
        current = self.is_muted()
        if current is None:
            return False
        return self.mute_master_volume(not current)
    
    def adjust_volume(self, delta: int) -> bool:
        """
        Adjust volume by a relative amount.
        
        Args:
            delta: Amount to adjust (+/- percentage points).
                   Positive values increase, negative decrease.
                   
        Returns:
            True if successful, False otherwise.
            
        Example:
            >>> audio = AudioController()
            >>> audio.adjust_volume(10)   # Increase by 10%
            >>> audio.adjust_volume(-5)   # Decrease by 5%
        """
        current = self.get_volume()
        if current is None:
            return False
        return self.set_master_volume(current + delta)
    
    @staticmethod
    def get_audio_sessions() -> List[Dict[str, Any]]:
        """
        Get all active audio sessions (applications playing audio).
        
        Returns:
            List of dictionaries with session info:
            - name: Application name
            - pid: Process ID
            - volume: Current volume (0-100)
            - muted: Whether the session is muted
            
        Example:
            >>> sessions = AudioController.get_audio_sessions()
            >>> for s in sessions:
            ...     print(f"{s['name']}: {s['volume']}%")
        """
        sessions = []
        
        try:
            from pycaw.pycaw import AudioUtilities
            
            for session in AudioUtilities.GetAllSessions():
                if session.Process:
                    try:
                        volume_interface = session.SimpleAudioVolume
                        sessions.append({
                            "name": session.Process.name(),
                            "pid": session.Process.pid,
                            "volume": round(volume_interface.GetMasterVolume() * 100, 1),
                            "muted": bool(volume_interface.GetMute()),
                        })
                    except Exception:
                        pass  # Skip sessions with access issues
                        
        except ImportError:
            logger.error("pycaw not installed")
        except Exception as e:
            logger.error(f"Failed to get audio sessions: {e}")
            
        return sessions
    
    def set_app_volume(self, app_name: str, level_percent: float) -> bool:
        """
        Set volume for a specific application.
        
        Args:
            app_name: Name of the application (e.g., "chrome.exe", "spotify.exe")
            level_percent: Volume level (0-100)
            
        Returns:
            True if successful, False if app not found or error.
        """
        try:
            from pycaw.pycaw import AudioUtilities
            
            app_name_lower = app_name.lower()
            level = max(0, min(100, float(level_percent))) / 100.0
            
            for session in AudioUtilities.GetAllSessions():
                if session.Process:
                    if session.Process.name().lower() == app_name_lower:
                        session.SimpleAudioVolume.SetMasterVolume(level, None)
                        logger.info(f"Set {app_name} volume to {level_percent}%")
                        return True
                        
            logger.warning(f"Application '{app_name}' not found in audio sessions")
            return False
            
        except Exception as e:
            logger.error(f"Failed to set app volume: {e}")
            return False


# ============================================================================
# Display Control
# ============================================================================

def get_brightness() -> Optional[Union[int, List[int]]]:
    """
    Get the current display brightness level(s).
    
    Returns:
        - Single integer (0-100) for one display
        - List of integers for multiple displays
        - None if brightness control is not available
        
    Note:
        External monitors require DDC/CI support. Laptops typically
        support brightness control through the display driver.
        
    Example:
        >>> brightness = get_brightness()
        >>> print(f"Current brightness: {brightness}%")
    """
    try:
        import screen_brightness_control as sbc
        
        brightness = sbc.get_brightness()
        
        if isinstance(brightness, list):
            if len(brightness) == 1:
                return brightness[0]
            return brightness
        return brightness
        
    except ImportError:
        logger.error("screen_brightness_control not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to get brightness: {e}")
        return None


def set_brightness(level: int, display: Optional[int] = None) -> bool:
    """
    Set the display brightness level.
    
    Args:
        level: Brightness level (0-100). Values outside range are clamped.
        display: Optional display index (0-based). None = all displays.
        
    Returns:
        True if successful, False otherwise.
        
    Raises:
        No exceptions - all errors are caught and logged.
        
    Note:
        - Laptop displays typically support brightness control
        - External monitors require DDC/CI support enabled
        - Some virtual displays may not support brightness control
        
    Example:
        >>> set_brightness(75)  # Set all displays to 75%
        True
        >>> set_brightness(50, display=0)  # Set first display to 50%
        True
    """
    try:
        import screen_brightness_control as sbc
        
        # Clamp value to valid range
        level = max(0, min(100, int(level)))
        
        if display is not None:
            sbc.set_brightness(level, display=display)
            logger.info(f"Brightness set to {level}% on display {display}")
        else:
            sbc.set_brightness(level)
            logger.info(f"Brightness set to {level}% on all displays")
            
        return True
        
    except ImportError:
        logger.error("screen_brightness_control not installed")
        return False
    except PermissionError:
        logger.error("Permission denied: Cannot control display brightness")
        return False
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle common DDC/CI failures
        if "ddc" in error_msg or "monitor" in error_msg:
            logger.warning(
                f"Display does not support DDC/CI brightness control: {e}"
            )
        elif "no" in error_msg and "method" in error_msg:
            logger.warning(
                "No compatible brightness control method available for this display"
            )
        else:
            logger.error(f"Failed to set brightness: {e}")
            
        return False


def adjust_brightness(delta: int) -> bool:
    """
    Adjust brightness by a relative amount.
    
    Args:
        delta: Amount to adjust (+/- percentage points).
        
    Returns:
        True if successful, False otherwise.
        
    Example:
        >>> adjust_brightness(10)   # Increase by 10%
        >>> adjust_brightness(-20)  # Decrease by 20%
    """
    current = get_brightness()
    if current is None:
        return False
        
    # Handle multiple displays - adjust the first one
    if isinstance(current, list):
        current = current[0] if current else 50
        
    return set_brightness(current + delta)


def get_displays() -> List[Dict[str, Any]]:
    """
    Get information about connected displays.
    
    Returns:
        List of dictionaries with display info:
        - name: Display name/identifier
        - brightness: Current brightness (if available)
        - method: Brightness control method used
        
    Example:
        >>> displays = get_displays()
        >>> for d in displays:
        ...     print(f"{d['name']}: {d.get('brightness', 'N/A')}%")
    """
    displays = []
    
    try:
        import screen_brightness_control as sbc
        
        for monitor in sbc.list_monitors():
            try:
                brightness = sbc.get_brightness(display=monitor)
                if isinstance(brightness, list):
                    brightness = brightness[0] if brightness else None
                    
                displays.append({
                    "name": monitor,
                    "brightness": brightness,
                    "controllable": True,
                })
            except Exception:
                displays.append({
                    "name": monitor,
                    "brightness": None,
                    "controllable": False,
                })
                
    except ImportError:
        logger.error("screen_brightness_control not installed")
    except Exception as e:
        logger.error(f"Failed to list displays: {e}")
        
    return displays


# ============================================================================
# Application Management
# ============================================================================

# Common application paths for intelligent lookup
COMMON_APP_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "notepad": [r"C:\Windows\System32\notepad.exe"],
    "explorer": [r"C:\Windows\explorer.exe"],
    "code": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "vscode": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    ],
    "discord": [
        os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
    ],
    "slack": [
        os.path.expandvars(r"%LOCALAPPDATA%\slack\slack.exe"),
    ],
    "terminal": [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"),
    ],
    "powershell": [
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    ],
    "cmd": [r"C:\Windows\System32\cmd.exe"],
    "calculator": [r"calc.exe"],  # Uses shell
    "paint": [r"mspaint.exe"],
}


def _find_executable(app_name: str) -> Optional[str]:
    """
    Find the executable path for an application.
    
    Args:
        app_name: Application name or path.
        
    Returns:
        Full path to executable, or None if not found.
    """
    # If it's already a valid path, return it
    if os.path.isfile(app_name):
        return app_name
        
    # Check if it has a valid extension
    if Path(app_name).suffix.lower() in ('.exe', '.bat', '.cmd', '.ps1'):
        # Try finding it in PATH
        import shutil
        found = shutil.which(app_name)
        if found:
            return found
    
    # Look up in common paths
    app_key = app_name.lower().replace('.exe', '').replace(' ', '')
    
    if app_key in COMMON_APP_PATHS:
        for path in COMMON_APP_PATHS[app_key]:
            expanded = os.path.expandvars(path)
            if os.path.isfile(expanded):
                return expanded
    
    # Try shutil.which for PATH lookup
    import shutil
    found = shutil.which(app_name)
    if found:
        return found
        
    # Try with .exe extension
    found = shutil.which(f"{app_name}.exe")
    if found:
        return found
        
    return None


def launch_app(
    app_name: str,
    args: Optional[List[str]] = None,
    working_dir: Optional[str] = None,
    wait: bool = False,
    shell: bool = False,
) -> Dict[str, Any]:
    """
    Launch an application.
    
    Args:
        app_name: Application name, path, or command.
                  Examples: "chrome", "notepad", "C:\\Program Files\\app.exe"
        args: Optional list of command-line arguments.
        working_dir: Optional working directory for the process.
        wait: If True, wait for the process to complete.
        shell: If True, run through shell (enables 'start' command behavior).
        
    Returns:
        Dictionary with launch result:
        - success: True if launched successfully
        - pid: Process ID (if available and not using shell)
        - path: Path to executable used
        - error: Error message if failed
        
    Example:
        >>> launch_app("chrome")
        {'success': True, 'pid': 12345, 'path': 'C:\\...\\chrome.exe'}
        
        >>> launch_app("notepad", args=["file.txt"])
        {'success': True, 'pid': 12346, ...}
        
        >>> launch_app("calculator")  # Uses shell for Windows Store apps
        {'success': True, ...}
    """
    result = {"success": False, "pid": None, "path": None, "error": None}
    
    try:
        # Find the executable
        exe_path = _find_executable(app_name)
        
        if exe_path:
            result["path"] = exe_path
            cmd = [exe_path]
            if args:
                cmd.extend(args)
                
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=working_dir,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                
                if wait:
                    process.wait()
                    
                result["success"] = True
                result["pid"] = process.pid
                logger.info(f"Launched {app_name} (PID: {process.pid})")
                return result
                
            except OSError as e:
                # Fall through to shell method
                logger.debug(f"Direct launch failed, trying shell: {e}")
                
        # Fallback: Use shell 'start' command
        cmd = f'start "" "{app_name}"'
        if args:
            cmd += ' ' + ' '.join(f'"{a}"' for a in args)
            
        subprocess.Popen(
            cmd,
            shell=True,
            cwd=working_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        result["success"] = True
        result["path"] = app_name
        logger.info(f"Launched {app_name} via shell")
        return result
        
    except FileNotFoundError:
        result["error"] = f"Application not found: {app_name}"
        logger.error(result["error"])
    except PermissionError:
        result["error"] = f"Permission denied launching: {app_name}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Failed to launch {app_name}: {e}"
        logger.error(result["error"])
        
    return result


def close_app(
    app_name: str,
    force: bool = False,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """
    Close an application gracefully, with force kill fallback.
    
    Args:
        app_name: Application name or process name (e.g., "chrome", "notepad.exe").
        force: If True, skip graceful termination and force kill immediately.
        timeout: Seconds to wait for graceful termination before force kill.
        
    Returns:
        Dictionary with close result:
        - success: True if at least one process was closed
        - terminated: Number of processes gracefully terminated
        - killed: Number of processes force killed
        - not_found: True if no matching processes were found
        - error: Error message if failed
        
    Example:
        >>> close_app("notepad")
        {'success': True, 'terminated': 1, 'killed': 0}
        
        >>> close_app("chrome", force=True)
        {'success': True, 'terminated': 0, 'killed': 3}
    """
    result = {
        "success": False,
        "terminated": 0,
        "killed": 0,
        "not_found": False,
        "error": None,
    }
    
    try:
        import psutil
        
        # Normalize the app name
        app_name_lower = app_name.lower()
        if not app_name_lower.endswith('.exe'):
            app_name_lower += '.exe'
            
        # Find matching processes
        matching_procs = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == app_name_lower:
                    matching_procs.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        if not matching_procs:
            result["not_found"] = True
            result["error"] = f"No process found matching: {app_name}"
            logger.warning(result["error"])
            return result
            
        for proc in matching_procs:
            try:
                if force:
                    proc.kill()
                    result["killed"] += 1
                    logger.info(f"Force killed {app_name} (PID: {proc.pid})")
                else:
                    # Try graceful termination first
                    proc.terminate()
                    
                    try:
                        proc.wait(timeout=timeout)
                        result["terminated"] += 1
                        logger.info(f"Terminated {app_name} (PID: {proc.pid})")
                    except psutil.TimeoutExpired:
                        # Force kill if graceful termination fails
                        proc.kill()
                        result["killed"] += 1
                        logger.warning(
                            f"Force killed {app_name} (PID: {proc.pid}) "
                            f"after {timeout}s timeout"
                        )
                        
            except psutil.NoSuchProcess:
                # Process already ended
                result["terminated"] += 1
            except psutil.AccessDenied:
                result["error"] = f"Access denied closing process (PID: {proc.pid})"
                logger.error(result["error"])
                continue
                
        result["success"] = (result["terminated"] + result["killed"]) > 0
        return result
        
    except ImportError:
        result["error"] = "psutil not installed"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Failed to close {app_name}: {e}"
        logger.error(result["error"])
        
    return result


def focus_window(
    title_or_app: str,
    exact_match: bool = False,
) -> Dict[str, Any]:
    """
    Bring a window to the foreground.
    
    Args:
        title_or_app: Window title substring or application name.
                      Examples: "Chrome", "Untitled - Notepad", "code"
        exact_match: If True, require exact title match.
        
    Returns:
        Dictionary with focus result:
        - success: True if window was focused
        - window_title: Full title of the focused window
        - not_found: True if no matching window was found
        - error: Error message if failed
        
    Example:
        >>> focus_window("Chrome")
        {'success': True, 'window_title': 'Google - Google Chrome'}
        
        >>> focus_window("Notepad")
        {'success': True, 'window_title': 'Untitled - Notepad'}
    """
    result = {
        "success": False,
        "window_title": None,
        "not_found": False,
        "error": None,
    }
    
    try:
        import pygetwindow as gw
        
        search_term = title_or_app.lower()
        
        # Get all windows
        windows = gw.getAllWindows()
        
        # Find matching window
        matching_window = None
        
        for window in windows:
            title = window.title.strip()
            if not title:  # Skip windows with empty titles
                continue
                
            title_lower = title.lower()
            
            if exact_match:
                if title_lower == search_term:
                    matching_window = window
                    break
            else:
                # Check if search term is in title
                if search_term in title_lower:
                    matching_window = window
                    break
                    
                # Also check for app name matches
                # e.g., "chrome" matches "Google Chrome" 
                if search_term in title_lower.split(' - ')[-1].lower():
                    matching_window = window
                    break
                    
        if matching_window is None:
            # Try getting windows with the app name in their exe
            try:
                import psutil
                
                for proc in psutil.process_iter(['name', 'pid']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if search_term in proc_name:
                            # Find windows belonging to this process
                            for window in windows:
                                if window.title.strip():
                                    # Check if this window might belong to the process
                                    # (pygetwindow doesn't directly expose PID)
                                    if any(word in window.title.lower() 
                                           for word in search_term.split()):
                                        matching_window = window
                                        break
                            if matching_window:
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                pass
                
        if matching_window is None:
            result["not_found"] = True
            result["error"] = f"No window found matching: {title_or_app}"
            logger.warning(result["error"])
            return result
            
        # Restore if minimized
        if matching_window.isMinimized:
            matching_window.restore()
            time.sleep(0.1)  # Brief delay for restore
            
        # Bring to foreground
        matching_window.activate()
        
        result["success"] = True
        result["window_title"] = matching_window.title
        logger.info(f"Focused window: {matching_window.title}")
        return result
        
    except ImportError:
        result["error"] = "pygetwindow not installed"
        logger.error(result["error"])
    except Exception as e:
        # Common exception: window cannot be activated
        if "Error code from Windows" in str(e):
            # Try alternative method using win32gui
            try:
                import win32gui
                import win32con
                
                def enum_callback(hwnd, results):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title and search_term.lower() in title.lower():
                            results.append((hwnd, title))
                            
                results = []
                win32gui.EnumWindows(enum_callback, results)
                
                if results:
                    hwnd, title = results[0]
                    
                    # Restore if minimized
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        
                    # Bring to front
                    win32gui.SetForegroundWindow(hwnd)
                    
                    result["success"] = True
                    result["window_title"] = title
                    logger.info(f"Focused window (via win32): {title}")
                    return result
                    
            except ImportError:
                pass
            except Exception as e2:
                result["error"] = f"Failed to focus window: {e2}"
                logger.error(result["error"])
                return result
                
        result["error"] = f"Failed to focus window: {e}"
        logger.error(result["error"])
        
    return result


def list_windows() -> List[Dict[str, Any]]:
    """
    List all visible windows.
    
    Returns:
        List of dictionaries with window info:
        - title: Window title
        - visible: Whether window is visible
        - minimized: Whether window is minimized
        - position: (x, y) position
        - size: (width, height) size
        
    Example:
        >>> windows = list_windows()
        >>> for w in windows:
        ...     print(w['title'])
    """
    windows = []
    
    try:
        import pygetwindow as gw
        
        for window in gw.getAllWindows():
            title = window.title.strip()
            if title:  # Skip windows with empty titles
                windows.append({
                    "title": title,
                    "visible": window.visible,
                    "minimized": window.isMinimized,
                    "position": (window.left, window.top),
                    "size": (window.width, window.height),
                })
                
    except ImportError:
        logger.error("pygetwindow not installed")
    except Exception as e:
        logger.error(f"Failed to list windows: {e}")
        
    return windows


def get_running_processes(name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get list of running processes.
    
    Args:
        name_filter: Optional substring to filter process names.
        
    Returns:
        List of dictionaries with process info:
        - name: Process name
        - pid: Process ID
        - memory_mb: Memory usage in MB
        - cpu_percent: CPU usage percentage
        
    Example:
        >>> processes = get_running_processes("chrome")
        >>> for p in processes:
        ...     print(f"{p['name']} (PID: {p['pid']}): {p['memory_mb']}MB")
    """
    processes = []
    
    try:
        import psutil
        
        for proc in psutil.process_iter(['name', 'pid', 'memory_info', 'cpu_percent']):
            try:
                info = proc.info
                name = info['name']
                
                # Apply filter if specified
                if name_filter and name_filter.lower() not in name.lower():
                    continue
                    
                memory = info['memory_info']
                memory_mb = memory.rss / (1024 * 1024) if memory else 0
                
                processes.append({
                    "name": name,
                    "pid": info['pid'],
                    "memory_mb": round(memory_mb, 1),
                    "cpu_percent": info['cpu_percent'] or 0,
                })
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
    except ImportError:
        logger.error("psutil not installed")
    except Exception as e:
        logger.error(f"Failed to list processes: {e}")
        
    return processes
