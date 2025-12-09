"""
The Sovereign Desktop - Perception Module

This module handles sensory input:
- Vision: Screen capture and processing
- OCR: Text extraction from screen
- Listeners: Event monitoring (keyboard, mouse)
"""

from .vision import VisionProcessor, ScreenCapture
from .ocr import OCREngine
from .listeners import EventListener, KeyboardListener, MouseListener

__all__ = [
    "VisionProcessor",
    "ScreenCapture",
    "OCREngine",
    "EventListener",
    "KeyboardListener",
    "MouseListener",
]
