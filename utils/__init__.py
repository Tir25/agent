"""
The Sovereign Desktop - Utilities Module

Common utilities for configuration and logging.
"""

from .config import Config, load_config, save_config
from .logging import setup_logging, get_logger

__all__ = [
    "Config",
    "load_config",
    "save_config",
    "setup_logging",
    "get_logger",
]
