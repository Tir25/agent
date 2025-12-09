"""
The Sovereign Desktop - Interfaces Module

This module handles human interaction:
- TTS: Text-to-Speech synthesis
- STT: Speech-to-Text recognition
- Voice Loop: Continuous voice interaction management
"""

from .tts import TextToSpeech, TTSEngine
from .stt import SpeechToText, STTEngine
from .voice_loop import VoiceLoop, VoiceLoopConfig

__all__ = [
    "TextToSpeech",
    "TTSEngine",
    "SpeechToText",
    "STTEngine",
    "VoiceLoop",
    "VoiceLoopConfig",
]
