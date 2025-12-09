"""
Logging Infrastructure

Provides centralized logging configuration with:
- File rotation
- Console output with colors
- Structured logging support
- Module-specific loggers
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


# ANSI color codes for console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        record.levelname = f"{color}{record.levelname:8}{Colors.RESET}"
        
        # Color the logger name
        record.name = f"{Colors.BLUE}{record.name}{Colors.RESET}"
        
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_size_mb: int = 100,
    backup_count: int = 5,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Set up application-wide logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for console only)
        max_size_mb: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        log_format: Custom log format string
        
    Returns:
        Root logger
    """
    # Default format
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Use colored formatter for console
    if sys.stdout.isatty():
        console_formatter = ColoredFormatter(log_format)
    else:
        console_formatter = logging.Formatter(log_format)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    root_logger.info(f"Logging initialized (level: {level})")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter with context support.
    
    Allows adding persistent context to log messages.
    """
    
    def __init__(self, logger: logging.Logger, context: dict = None):
        super().__init__(logger, context or {})
    
    def process(self, msg, kwargs):
        # Add context to message if present
        if self.extra:
            context_str = " | ".join(f"{k}={v}" for k, v in self.extra.items())
            msg = f"[{context_str}] {msg}"
        return msg, kwargs
    
    def with_context(self, **kwargs) -> "LoggerAdapter":
        """Create a new adapter with additional context."""
        new_extra = {**self.extra, **kwargs}
        return LoggerAdapter(self.logger, new_extra)


def log_exception(logger: logging.Logger, exc: Exception, message: str = "An error occurred"):
    """
    Log an exception with full traceback.
    
    Args:
        logger: Logger to use
        exc: Exception to log
        message: Additional message
    """
    import traceback
    
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(f"{message}: {exc}\n{tb}")


class LogCapture:
    """
    Context manager to capture log output.
    
    Useful for testing or capturing logs for display.
    """
    
    def __init__(self, logger_name: str = None, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.handler = None
        self.records: list[logging.LogRecord] = []
    
    def __enter__(self):
        # Create a handler that captures records
        class CaptureHandler(logging.Handler):
            def __init__(self, records_list):
                super().__init__()
                self.records = records_list
            
            def emit(self, record):
                self.records.append(record)
        
        self.handler = CaptureHandler(self.records)
        self.handler.setLevel(self.level)
        
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)
        
        return self
    
    def __exit__(self, *args):
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self.handler)
    
    @property
    def messages(self) -> list[str]:
        """Get captured messages as strings."""
        return [record.getMessage() for record in self.records]
    
    def has_message(self, substring: str) -> bool:
        """Check if any message contains the substring."""
        return any(substring in msg for msg in self.messages)
