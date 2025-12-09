"""
The Sovereign Desktop
Your AI, Your Machine, Your Rules.

A local-first, multimodal Windows agent powered by Llama 3.2 Vision.
"""

__version__ = "0.1.0"
__author__ = "Sovereign Desktop Team"


from core import LLMEngine, SemanticRouter, ContextManager
from utils import setup_logging, load_config

__all__ = [
    "LLMEngine",
    "SemanticRouter", 
    "ContextManager",
    "setup_logging",
    "load_config",
]
