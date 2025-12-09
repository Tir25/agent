"""
Services Package

Concrete implementations of tools and services.

Each service file contains one or more tools that implement
the BaseTool interface from app/interfaces/.

Services are organized by domain:
- system/: Volume, brightness, process management
- office/: Microsoft Word, Excel automation
"""

from .system import VolumeControlTool, BrightnessControlTool, ProcessManagerTool
from .office import WordWriterTool, ExcelReaderTool

__all__ = [
    # System
    "VolumeControlTool",
    "BrightnessControlTool",
    "ProcessManagerTool",
    # Office
    "WordWriterTool",
    "ExcelReaderTool",
]
