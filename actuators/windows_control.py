"""
Windows Control - OS-level Automation

Provides comprehensive Windows automation capabilities including:
- Keyboard and mouse input simulation
- Window management
- Application launching
- Clipboard operations
- File system operations
"""

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about a window."""
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]  # left, top, right, bottom
    is_visible: bool
    process_id: int


class WindowsController:
    """
    Windows OS automation controller.
    
    Provides comprehensive automation capabilities for Windows,
    running entirely locally without any external services.
    """
    
    def __init__(self):
        """Initialize the Windows controller."""
        self._init_dependencies()
        logger.info("Windows Controller initialized")
    
    def _init_dependencies(self):
        """Lazy load Windows-specific dependencies."""
        try:
            import pyautogui
            import win32gui
            import win32con
            import win32process
            import win32api
            
            self._pyautogui = pyautogui
            self._win32gui = win32gui
            self._win32con = win32con
            self._win32process = win32process
            self._win32api = win32api
            
            # Configure pyautogui
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
            pyautogui.PAUSE = 0.1  # Small delay between actions
            
        except ImportError as e:
            raise ImportError(f"Required package not installed: {e}")
    
    # ==================== Keyboard Control ====================
    
    def type_text(self, text: str, interval: float = 0.05):
        """
        Type text using keyboard simulation.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
        """
        self._pyautogui.write(text, interval=interval)
        logger.debug(f"Typed: {text[:50]}...")
    
    def press_key(self, key: str):
        """
        Press a single key.
        
        Args:
            key: Key name (e.g., "enter", "tab", "escape")
        """
        self._pyautogui.press(key)
        logger.debug(f"Pressed: {key}")
    
    def hotkey(self, *keys: str):
        """
        Press a key combination.
        
        Args:
            keys: Keys to press together (e.g., "ctrl", "c")
        """
        self._pyautogui.hotkey(*keys)
        logger.debug(f"Hotkey: {'+'.join(keys)}")
    
    def key_down(self, key: str):
        """Hold down a key."""
        self._pyautogui.keyDown(key)
    
    def key_up(self, key: str):
        """Release a key."""
        self._pyautogui.keyUp(key)
    
    # ==================== Mouse Control ====================
    
    def move_mouse(self, x: int, y: int, duration: float = 0.2):
        """
        Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Animation duration in seconds
        """
        self._pyautogui.moveTo(x, y, duration=duration)
        logger.debug(f"Mouse moved to: ({x}, {y})")
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left"):
        """
        Click at coordinates or current position.
        
        Args:
            x: X coordinate (None for current)
            y: Y coordinate (None for current)
            button: "left", "right", or "middle"
        """
        if x is not None and y is not None:
            self._pyautogui.click(x, y, button=button)
        else:
            self._pyautogui.click(button=button)
        logger.debug(f"Clicked: {button} at ({x}, {y})")
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Double-click at coordinates."""
        if x is not None and y is not None:
            self._pyautogui.doubleClick(x, y)
        else:
            self._pyautogui.doubleClick()
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Right-click at coordinates."""
        self.click(x, y, button="right")
    
    def scroll(self, amount: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        Scroll the mouse wheel.
        
        Args:
            amount: Positive = up, negative = down
            x, y: Optional position to scroll at
        """
        self._pyautogui.scroll(amount, x, y)
        logger.debug(f"Scrolled: {amount}")
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5):
        """Drag from one point to another."""
        self._pyautogui.moveTo(start_x, start_y)
        self._pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
    
    # ==================== Window Management ====================
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get information about the active window."""
        hwnd = self._win32gui.GetForegroundWindow()
        return self._get_window_info(hwnd)
    
    def get_all_windows(self) -> List[WindowInfo]:
        """Get all visible windows."""
        windows = []
        
        def callback(hwnd, _):
            if self._win32gui.IsWindowVisible(hwnd):
                info = self._get_window_info(hwnd)
                if info and info.title:
                    windows.append(info)
            return True
        
        self._win32gui.EnumWindows(callback, None)
        return windows
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """Find a window by title (partial match)."""
        title_lower = title.lower()
        for window in self.get_all_windows():
            if title_lower in window.title.lower():
                return window
        return None
    
    def focus_window(self, hwnd: int) -> bool:
        """Bring a window to the foreground."""
        try:
            self._win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
            return False
    
    def minimize_window(self, hwnd: int):
        """Minimize a window."""
        self._win32gui.ShowWindow(hwnd, self._win32con.SW_MINIMIZE)
    
    def maximize_window(self, hwnd: int):
        """Maximize a window."""
        self._win32gui.ShowWindow(hwnd, self._win32con.SW_MAXIMIZE)
    
    def restore_window(self, hwnd: int):
        """Restore a window."""
        self._win32gui.ShowWindow(hwnd, self._win32con.SW_RESTORE)
    
    def close_window(self, hwnd: int):
        """Close a window."""
        self._win32gui.PostMessage(hwnd, self._win32con.WM_CLOSE, 0, 0)
    
    def _get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """Get WindowInfo for a window handle."""
        try:
            title = self._win32gui.GetWindowText(hwnd)
            class_name = self._win32gui.GetClassName(hwnd)
            rect = self._win32gui.GetWindowRect(hwnd)
            is_visible = self._win32gui.IsWindowVisible(hwnd)
            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)
            
            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                rect=rect,
                is_visible=bool(is_visible),
                process_id=pid,
            )
        except Exception:
            return None
    
    # ==================== Application Control ====================
    
    def launch_application(self, path_or_name: str, args: List[str] = None) -> bool:
        """
        Launch an application.
        
        Args:
            path_or_name: Full path or executable name
            args: Optional command line arguments
            
        Returns:
            True if launched successfully
        """
        try:
            cmd = [path_or_name] + (args or [])
            subprocess.Popen(cmd, shell=True)
            logger.info(f"Launched: {path_or_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch {path_or_name}: {e}")
            return False
    
    def open_file(self, path: str) -> bool:
        """Open a file with the default application."""
        import os
        try:
            os.startfile(path)
            return True
        except Exception as e:
            logger.error(f"Failed to open {path}: {e}")
            return False
    
    def open_url(self, url: str) -> bool:
        """Open a URL in the default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            logger.error(f"Failed to open URL: {e}")
            return False
    
    # ==================== Clipboard Operations ====================
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        self._pyautogui.write(text)
        import pyperclip
        pyperclip.copy(text)
        logger.debug(f"Copied to clipboard: {text[:50]}...")
    
    def get_clipboard(self) -> str:
        """Get text from clipboard."""
        import pyperclip
        return pyperclip.paste()
    
    def paste(self):
        """Paste from clipboard."""
        self.hotkey("ctrl", "v")
    
    def copy(self):
        """Copy selection to clipboard."""
        self.hotkey("ctrl", "c")
    
    def cut(self):
        """Cut selection to clipboard."""
        self.hotkey("ctrl", "x")
    
    # ==================== System Operations ====================
    
    def lock_screen(self):
        """Lock the Windows screen."""
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        logger.info("Screen locked")
    
    def sleep(self):
        """Put the computer to sleep."""
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    
    def shutdown(self, delay: int = 30):
        """
        Shutdown the computer.
        
        Args:
            delay: Delay in seconds before shutdown
        """
        subprocess.run(["shutdown", "/s", "/t", str(delay)])
        logger.warning(f"Shutdown initiated in {delay} seconds")
    
    def restart(self, delay: int = 30):
        """Restart the computer."""
        subprocess.run(["shutdown", "/r", "/t", str(delay)])
        logger.warning(f"Restart initiated in {delay} seconds")
    
    def cancel_shutdown(self):
        """Cancel a pending shutdown."""
        subprocess.run(["shutdown", "/a"])
        logger.info("Shutdown cancelled")
    
    # ==================== Screen Information ====================
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the primary screen resolution."""
        return self._pyautogui.size()
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return self._pyautogui.position()
    
    def locate_on_screen(self, image_path: str, confidence: float = 0.9) -> Optional[Tuple[int, int]]:
        """
        Find an image on screen.
        
        Args:
            image_path: Path to the image to find
            confidence: Match confidence (0.0 - 1.0)
            
        Returns:
            (x, y) center coordinates if found, None otherwise
        """
        try:
            location = self._pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            return location
        except Exception:
            return None
