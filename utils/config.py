"""
Configuration Management

Handles loading, saving, and validating configuration
from YAML files with environment variable support.
"""

import os
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM configuration."""
    model: str = "llama3.2-vision"
    host: str = "http://localhost:11434"
    temperature: float = 0.7
    context_length: int = 8192


@dataclass
class VoiceConfig:
    """Voice interaction configuration."""
    stt_engine: str = "faster_whisper"
    stt_model: str = "base"
    tts_engine: str = "sapi"
    tts_voice: Optional[str] = None
    wake_word: Optional[str] = None
    push_to_talk_key: str = "ctrl+space"
    language: str = "en"


@dataclass
class VisionConfig:
    """Vision processing configuration."""
    capture_interval: float = 1.0
    max_resolution: tuple = (1920, 1080)
    ocr_enabled: bool = True
    ocr_backend: str = "tesseract"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[str] = "logs/sovereign.log"
    max_size_mb: int = 100
    backup_count: int = 5
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


@dataclass
class Config:
    """Main application configuration."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # General settings
    debug: bool = False
    data_dir: str = "data"
    plugins_dir: str = "plugins"


def load_config(path: Optional[Path] = None) -> Config:
    """
    Load configuration from a YAML file.
    
    Supports environment variable interpolation using ${VAR} syntax.
    Falls back to defaults if file doesn't exist.
    
    Args:
        path: Path to config file (default: config.yaml)
        
    Returns:
        Config object
    """
    if path is None:
        path = Path("config.yaml")
    else:
        path = Path(path)
    
    config = Config()
    
    if not path.exists():
        logger.warning(f"Config file not found: {path}, using defaults")
        return config
    
    try:
        import yaml
        
        with open(path, "r") as f:
            raw_config = yaml.safe_load(f)
        
        if raw_config:
            config = _parse_config(raw_config)
            logger.info(f"Loaded config from {path}")
            
    except ImportError:
        logger.warning("PyYAML not installed, using default config")
    except Exception as e:
        logger.error(f"Failed to load config: {e}, using defaults")
    
    return config


def save_config(config: Config, path: Optional[Path] = None):
    """
    Save configuration to a YAML file.
    
    Args:
        config: Config object to save
        path: Path to save to (default: config.yaml)
    """
    if path is None:
        path = Path("config.yaml")
    else:
        path = Path(path)
    
    try:
        import yaml
        
        # Convert dataclasses to dicts
        config_dict = _config_to_dict(config)
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved config to {path}")
        
    except ImportError:
        logger.error("PyYAML not installed, cannot save config")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")


def _parse_config(raw: Dict[str, Any]) -> Config:
    """Parse raw config dict into Config object."""
    # Process environment variables
    raw = _interpolate_env_vars(raw)
    
    config = Config()
    
    if "llm" in raw:
        config.llm = LLMConfig(**{k: v for k, v in raw["llm"].items() if hasattr(LLMConfig, k)})
    
    if "voice" in raw:
        config.voice = VoiceConfig(**{k: v for k, v in raw["voice"].items() if hasattr(VoiceConfig, k)})
    
    if "vision" in raw:
        vision_data = raw["vision"]
        if "max_resolution" in vision_data and isinstance(vision_data["max_resolution"], list):
            vision_data["max_resolution"] = tuple(vision_data["max_resolution"])
        config.vision = VisionConfig(**{k: v for k, v in vision_data.items() if hasattr(VisionConfig, k)})
    
    if "logging" in raw:
        config.logging = LoggingConfig(**{k: v for k, v in raw["logging"].items() if hasattr(LoggingConfig, k)})
    
    # General settings
    if "debug" in raw:
        config.debug = raw["debug"]
    if "data_dir" in raw:
        config.data_dir = raw["data_dir"]
    if "plugins_dir" in raw:
        config.plugins_dir = raw["plugins_dir"]
    
    return config


def _interpolate_env_vars(obj: Any) -> Any:
    """Replace ${VAR} patterns with environment variable values."""
    import re
    
    if isinstance(obj, str):
        # Find ${VAR} patterns
        pattern = r'\$\{([^}]+)\}'
        
        def replace(match):
            var_name = match.group(1)
            default = None
            
            # Support ${VAR:-default} syntax
            if ":-" in var_name:
                var_name, default = var_name.split(":-", 1)
            
            return os.environ.get(var_name, default or match.group(0))
        
        return re.sub(pattern, replace, obj)
    
    elif isinstance(obj, dict):
        return {k: _interpolate_env_vars(v) for k, v in obj.items()}
    
    elif isinstance(obj, list):
        return [_interpolate_env_vars(item) for item in obj]
    
    return obj


def _config_to_dict(config: Config) -> Dict[str, Any]:
    """Convert Config object to dictionary."""
    return {
        "llm": asdict(config.llm),
        "voice": {k: v for k, v in asdict(config.voice).items() if v is not None},
        "vision": {
            **{k: v for k, v in asdict(config.vision).items() if k != "max_resolution"},
            "max_resolution": list(config.vision.max_resolution),
        },
        "logging": {k: v for k, v in asdict(config.logging).items() if v is not None},
        "debug": config.debug,
        "data_dir": config.data_dir,
        "plugins_dir": config.plugins_dir,
    }


def get_default_config_yaml() -> str:
    """Get the default configuration as YAML string."""
    return """# The Sovereign Desktop Configuration
# Your AI, Your Machine, Your Rules.

# LLM Settings (Ollama)
llm:
  model: "llama3.2-vision"
  host: "http://localhost:11434"
  temperature: 0.7
  context_length: 8192

# Voice Interaction
voice:
  stt_engine: "faster_whisper"  # faster_whisper, whisper, windows
  stt_model: "base"  # tiny, base, small, medium, large
  tts_engine: "sapi"  # sapi, piper, edge
  tts_voice: null  # null for default
  wake_word: null  # null to disable, or "hey sovereign"
  push_to_talk_key: "ctrl+space"
  language: "en"

# Vision Processing
vision:
  capture_interval: 1.0  # seconds
  max_resolution: [1920, 1080]
  ocr_enabled: true
  ocr_backend: "tesseract"  # tesseract, easyocr

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/sovereign.log"
  max_size_mb: 100
  backup_count: 5

# General
debug: false
data_dir: "data"
plugins_dir: "plugins"
"""
