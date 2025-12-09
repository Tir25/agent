"""
Event Listeners - Keyboard, Mouse, and System Event Monitoring

Provides non-blocking event listeners for tracking user input
and system events.
"""

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Optional, Set

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be listened for."""
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    MOUSE_CLICK = auto()
    MOUSE_MOVE = auto()
    MOUSE_SCROLL = auto()
    HOTKEY = auto()


@dataclass
class InputEvent:
    """Generic input event."""
    event_type: EventType
    timestamp: datetime
    data: dict


class EventListener(ABC):
    """Base class for event listeners."""
    
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable[[InputEvent], None]] = []
    
    def add_callback(self, callback: Callable[[InputEvent], None]):
        """Add an event callback."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[InputEvent], None]):
        """Remove an event callback."""
        self._callbacks.remove(callback)
    
    def _emit(self, event: InputEvent):
        """Emit an event to all callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    @abstractmethod
    def start(self):
        """Start listening for events."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop listening for events."""
        pass
    
    @property
    def is_running(self) -> bool:
        """Check if the listener is running."""
        return self._running


class KeyboardListener(EventListener):
    """
    Keyboard event listener using pynput.
    
    Supports individual key events and hotkey combinations.
    """
    
    def __init__(self):
        super().__init__()
        self._listener = None
        self._hotkeys: dict[frozenset, Callable] = {}
        self._pressed_keys: Set[str] = set()
    
    def register_hotkey(self, keys: tuple, callback: Callable):
        """
        Register a hotkey combination.
        
        Args:
            keys: Tuple of key names (e.g., ("ctrl", "shift", "a"))
            callback: Function to call when hotkey is pressed
        """
        self._hotkeys[frozenset(keys)] = callback
        logger.info(f"Registered hotkey: {'+'.join(keys)}")
    
    def unregister_hotkey(self, keys: tuple):
        """Unregister a hotkey combination."""
        self._hotkeys.pop(frozenset(keys), None)
    
    def start(self):
        """Start the keyboard listener."""
        if self._running:
            return
        
        try:
            from pynput import keyboard
            
            def on_press(key):
                key_name = self._get_key_name(key)
                self._pressed_keys.add(key_name)
                
                # Check for hotkeys
                current_combo = frozenset(self._pressed_keys)
                for hotkey, callback in self._hotkeys.items():
                    if hotkey <= current_combo:
                        callback()
                
                event = InputEvent(
                    event_type=EventType.KEY_PRESS,
                    timestamp=datetime.now(),
                    data={"key": key_name},
                )
                self._emit(event)
            
            def on_release(key):
                key_name = self._get_key_name(key)
                self._pressed_keys.discard(key_name)
                
                event = InputEvent(
                    event_type=EventType.KEY_RELEASE,
                    timestamp=datetime.now(),
                    data={"key": key_name},
                )
                self._emit(event)
            
            self._listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
            )
            self._listener.start()
            self._running = True
            logger.info("Keyboard listener started")
            
        except ImportError:
            raise ImportError("pynput not installed. Run: pip install pynput")
    
    def stop(self):
        """Stop the keyboard listener."""
        if self._listener:
            self._listener.stop()
            self._running = False
            logger.info("Keyboard listener stopped")
    
    def _get_key_name(self, key) -> str:
        """Get a normalized key name."""
        try:
            return key.char
        except AttributeError:
            return str(key).replace("Key.", "").lower()


class MouseListener(EventListener):
    """
    Mouse event listener using pynput.
    
    Tracks clicks, movements, and scrolling.
    """
    
    def __init__(self, track_movement: bool = False):
        """
        Initialize the mouse listener.
        
        Args:
            track_movement: Whether to track mouse movement (can be noisy)
        """
        super().__init__()
        self._listener = None
        self._track_movement = track_movement
    
    def start(self):
        """Start the mouse listener."""
        if self._running:
            return
        
        try:
            from pynput import mouse
            
            def on_click(x, y, button, pressed):
                event = InputEvent(
                    event_type=EventType.MOUSE_CLICK,
                    timestamp=datetime.now(),
                    data={
                        "x": x,
                        "y": y,
                        "button": str(button).replace("Button.", ""),
                        "pressed": pressed,
                    },
                )
                self._emit(event)
            
            def on_scroll(x, y, dx, dy):
                event = InputEvent(
                    event_type=EventType.MOUSE_SCROLL,
                    timestamp=datetime.now(),
                    data={"x": x, "y": y, "dx": dx, "dy": dy},
                )
                self._emit(event)
            
            def on_move(x, y):
                if self._track_movement:
                    event = InputEvent(
                        event_type=EventType.MOUSE_MOVE,
                        timestamp=datetime.now(),
                        data={"x": x, "y": y},
                    )
                    self._emit(event)
            
            self._listener = mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll,
                on_move=on_move,
            )
            self._listener.start()
            self._running = True
            logger.info("Mouse listener started")
            
        except ImportError:
            raise ImportError("pynput not installed. Run: pip install pynput")
    
    def stop(self):
        """Stop the mouse listener."""
        if self._listener:
            self._listener.stop()
            self._running = False
            logger.info("Mouse listener stopped")


class HotkeyManager:
    """
    Convenience class for managing global hotkeys.
    
    Uses keyboard listener internally but provides a simpler API.
    """
    
    def __init__(self):
        self._keyboard = KeyboardListener()
        self._hotkeys: dict[str, Callable] = {}
    
    def register(self, hotkey_string: str, callback: Callable):
        """
        Register a hotkey using a string notation.
        
        Args:
            hotkey_string: Hotkey notation (e.g., "ctrl+shift+a")
            callback: Function to call
        """
        keys = tuple(k.strip().lower() for k in hotkey_string.split("+"))
        self._keyboard.register_hotkey(keys, callback)
        self._hotkeys[hotkey_string] = callback
    
    def unregister(self, hotkey_string: str):
        """Unregister a hotkey."""
        if hotkey_string in self._hotkeys:
            keys = tuple(k.strip().lower() for k in hotkey_string.split("+"))
            self._keyboard.unregister_hotkey(keys)
            del self._hotkeys[hotkey_string]
    
    def start(self):
        """Start listening for hotkeys."""
        self._keyboard.start()
    
    def stop(self):
        """Stop listening for hotkeys."""
        self._keyboard.stop()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
