"""
Text-to-Speech - Voice Synthesis

Provides local text-to-speech capabilities using various engines:
- Piper (recommended, high quality, local)
- Edge TTS (online, free)
- Windows SAPI (built-in)
"""

import asyncio
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class TTSEngine(Enum):
    """Available TTS engines."""
    PIPER = "piper"
    EDGE = "edge"
    SAPI = "sapi"


@dataclass
class Voice:
    """Voice configuration."""
    id: str
    name: str
    language: str
    gender: str
    engine: TTSEngine


class BaseTTS(ABC):
    """Base class for TTS engines."""
    
    @abstractmethod
    def speak(self, text: str) -> bytes:
        """Synthesize text to audio bytes."""
        pass
    
    @abstractmethod
    async def speak_async(self, text: str) -> bytes:
        """Asynchronous speech synthesis."""
        pass
    
    @abstractmethod
    def get_voices(self) -> List[Voice]:
        """Get available voices."""
        pass


class TextToSpeech:
    """
    Text-to-Speech synthesis with multiple engine support.
    
    Prioritizes local, offline-capable engines for privacy.
    Falls back to online services when necessary.
    """
    
    def __init__(
        self,
        engine: TTSEngine = TTSEngine.SAPI,
        voice_id: Optional[str] = None,
        rate: float = 1.0,
        volume: float = 1.0,
    ):
        """
        Initialize TTS.
        
        Args:
            engine: TTS engine to use
            voice_id: Specific voice to use
            rate: Speech rate (0.5 - 2.0)
            volume: Volume level (0.0 - 1.0)
        """
        self.engine_type = engine
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        
        self._engine = self._init_engine(engine)
        logger.info(f"TTS initialized with {engine.value} engine")
    
    def _init_engine(self, engine: TTSEngine) -> BaseTTS:
        """Initialize the specified engine."""
        if engine == TTSEngine.PIPER:
            return PiperTTS(self.voice_id)
        elif engine == TTSEngine.EDGE:
            return EdgeTTS(self.voice_id)
        elif engine == TTSEngine.SAPI:
            return SapiTTS(self.voice_id, self.rate, self.volume)
        else:
            raise ValueError(f"Unknown engine: {engine}")
    
    def speak(self, text: str) -> bytes:
        """
        Synthesize text to audio.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio bytes (WAV format)
        """
        return self._engine.speak(text)
    
    async def speak_async(self, text: str) -> bytes:
        """Asynchronous speech synthesis."""
        return await self._engine.speak_async(text)
    
    def speak_to_file(self, text: str, path: Path) -> Path:
        """Synthesize text and save to file."""
        audio = self.speak(text)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(audio)
        return path
    
    def speak_and_play(self, text: str):
        """Synthesize and immediately play audio."""
        audio = self.speak(text)
        self._play_audio(audio)
    
    def _play_audio(self, audio_bytes: bytes):
        """Play audio bytes."""
        try:
            import sounddevice as sd
            import soundfile as sf
            from io import BytesIO
            
            data, samplerate = sf.read(BytesIO(audio_bytes))
            sd.play(data, samplerate)
            sd.wait()
        except ImportError:
            # Fallback: save to temp file and play with system
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            subprocess.run(
                ["cmd", "/c", "start", "/min", temp_path],
                shell=True,
                capture_output=True,
            )
    
    def get_voices(self) -> List[Voice]:
        """Get available voices for the current engine."""
        return self._engine.get_voices()
    
    def set_voice(self, voice_id: str):
        """Set the voice to use."""
        self.voice_id = voice_id
        self._engine = self._init_engine(self.engine_type)


class SapiTTS(BaseTTS):
    """Windows SAPI TTS engine (built-in, offline)."""
    
    def __init__(self, voice_id: Optional[str] = None, rate: float = 1.0, volume: float = 1.0):
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        self._init_sapi()
    
    def _init_sapi(self):
        """Initialize SAPI."""
        try:
            import win32com.client
            self._speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Set rate (-10 to 10, map from 0.5-2.0)
            self._speaker.Rate = int((self.rate - 1.0) * 10)
            
            # Set volume (0-100)
            self._speaker.Volume = int(self.volume * 100)
            
            # Set voice if specified
            if self.voice_id:
                for voice in self._speaker.GetVoices():
                    if self.voice_id in voice.GetDescription():
                        self._speaker.Voice = voice
                        break
                        
        except ImportError:
            raise ImportError("pywin32 not installed. Run: pip install pywin32")
    
    def speak(self, text: str) -> bytes:
        """Synthesize to WAV bytes."""
        import win32com.client
        from io import BytesIO
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        # Create file stream
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        stream.Open(temp_path, 3)  # SSFMCreateForWrite
        
        self._speaker.AudioOutputStream = stream
        self._speaker.Speak(text)
        stream.Close()
        
        with open(temp_path, "rb") as f:
            audio = f.read()
        
        Path(temp_path).unlink()
        return audio
    
    async def speak_async(self, text: str) -> bytes:
        """Async wrapper."""
        return await asyncio.to_thread(self.speak, text)
    
    def get_voices(self) -> List[Voice]:
        """Get available SAPI voices."""
        voices = []
        for voice in self._speaker.GetVoices():
            desc = voice.GetDescription()
            voices.append(Voice(
                id=desc,
                name=desc.split(" - ")[0] if " - " in desc else desc,
                language="en-US",
                gender="unknown",
                engine=TTSEngine.SAPI,
            ))
        return voices


class PiperTTS(BaseTTS):
    """Piper TTS engine (local, high quality)."""
    
    def __init__(self, voice_id: Optional[str] = None, model_path: Optional[Path] = None):
        self.voice_id = voice_id or "en_US-lessac-medium"
        self.model_path = model_path
    
    def speak(self, text: str) -> bytes:
        """Synthesize using Piper."""
        try:
            # Piper command line usage
            cmd = ["piper", "--model", self.voice_id, "--output_file", "-"]
            
            result = subprocess.run(
                cmd,
                input=text.encode(),
                capture_output=True,
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Piper failed: {result.stderr.decode()}")
            
            return result.stdout
            
        except FileNotFoundError:
            raise RuntimeError("Piper not found. Install from: https://github.com/rhasspy/piper")
    
    async def speak_async(self, text: str) -> bytes:
        """Async Piper synthesis."""
        return await asyncio.to_thread(self.speak, text)
    
    def get_voices(self) -> List[Voice]:
        """Get available Piper voices."""
        # Would need to scan model directory
        return [
            Voice(
                id="en_US-lessac-medium",
                name="Lessac (Medium)",
                language="en-US",
                gender="male",
                engine=TTSEngine.PIPER,
            ),
        ]


class EdgeTTS(BaseTTS):
    """Microsoft Edge TTS (online, free, high quality)."""
    
    def __init__(self, voice_id: Optional[str] = None):
        self.voice_id = voice_id or "en-US-AriaNeural"
    
    def speak(self, text: str) -> bytes:
        """Synthesize using Edge TTS."""
        return asyncio.run(self.speak_async(text))
    
    async def speak_async(self, text: str) -> bytes:
        """Async Edge TTS synthesis."""
        try:
            import edge_tts
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            communicate = edge_tts.Communicate(text, self.voice_id)
            await communicate.save(temp_path)
            
            with open(temp_path, "rb") as f:
                audio = f.read()
            
            Path(temp_path).unlink()
            return audio
            
        except ImportError:
            raise ImportError("edge-tts not installed. Run: pip install edge-tts")
    
    def get_voices(self) -> List[Voice]:
        """Get available Edge TTS voices."""
        # Common voices, full list available online
        return [
            Voice("en-US-AriaNeural", "Aria", "en-US", "female", TTSEngine.EDGE),
            Voice("en-US-GuyNeural", "Guy", "en-US", "male", TTSEngine.EDGE),
            Voice("en-GB-SoniaNeural", "Sonia", "en-GB", "female", TTSEngine.EDGE),
            Voice("en-AU-NatashaNeural", "Natasha", "en-AU", "female", TTSEngine.EDGE),
        ]
