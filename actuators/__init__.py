"""
The Sovereign Desktop - Actuators Module

This module handles action execution:
- Windows Control: OS-level automation
- Audio Control: Audio/media management
- Browser Agent: Web automation
- System Ops: Hardware and application control
- Office Ops: Microsoft Office COM automation
"""

from .windows_control import WindowsController
from .audio_control import AudioController
from .browser_agent import BrowserAgent
from .system_ops import (
    AudioController as SystemAudioController,
    get_brightness,
    set_brightness,
    adjust_brightness,
    get_displays,
    launch_app,
    close_app,
    focus_window,
    list_windows,
    get_running_processes,
)
from .office_ops import (
    append_text_to_doc,
    create_word_document,
    read_word_document,
    read_excel_data,
    write_excel_cell,
    write_excel_range,
    get_excel_info,
)

__all__ = [
    "WindowsController",
    "AudioController",
    "BrowserAgent",
    "SystemAudioController",
    "get_brightness",
    "set_brightness",
    "adjust_brightness",
    "get_displays",
    "launch_app",
    "close_app",
    "focus_window",
    "list_windows",
    "get_running_processes",
    "append_text_to_doc",
    "create_word_document",
    "read_word_document",
    "read_excel_data",
    "write_excel_cell",
    "write_excel_range",
    "get_excel_info",
]
