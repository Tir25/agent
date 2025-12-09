"""
AI Services Package

AI-powered tools for the Sovereign Desktop Agent:
- vision: Image analysis using VLM (llama3.2-vision)
- chat: General conversation using LLM (llama3.2:3b)
"""

from .vision import VisionTool
from .chat import ChatTool

__all__ = [
    "VisionTool",
    "ChatTool",
]

