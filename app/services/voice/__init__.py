"""
Voice Services Package

Voice I/O layer for the Sovereign Desktop Agent:
- Speaker (TextToSpeech): Voice output using pyttsx3
- Listener (VoiceListener): Voice input using Vosk
"""

from .speaker import TextToSpeech
from .listener import VoiceListener

__all__ = [
    "TextToSpeech",
    "VoiceListener",
]
