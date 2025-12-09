"""
Speech-to-Text - Voice Recognition

Provides local speech recognition capabilities using:
- Faster Whisper (recommended, local, accurate)
- Whisper.cpp (local, fast)
- Windows Speech Recognition (built-in)
"""

import asyncio
import logging
import tempfile
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Generator
import threading
import queue

logger = logging.getLogger(__name__)


class STTEngine(Enum):
    """Available STT engines."""
    FASTER_WHISPER = "faster_whisper"
    WHISPER = "whisper"
    WINDOWS = "windows"


@dataclass
class TranscriptionResult:
    """Result of speech transcription."""
    text: str
    confidence: float
    language: str
    segments: List[dict]
    duration: float


class BaseSpeechRecognizer(ABC):
    """Base class for speech recognizers."""
    
    @abstractmethod
    def transcribe(self, audio: bytes) -> TranscriptionResult:
        """Transcribe audio bytes."""
        pass
    
    @abstractmethod
    def transcribe_file(self, path: Path) -> TranscriptionResult:
        """Transcribe an audio file."""
        pass


class SpeechToText:
    """
    Speech-to-Text recognition with multiple engine support.
    
    Prioritizes local, offline-capable engines for privacy.
    Supports real-time streaming and file transcription.
    """
    
    def __init__(
        self,
        engine: STTEngine = STTEngine.FASTER_WHISPER,
        model_size: str = "base",
        language: str = "en",
        device: str = "cpu",
    ):
        """
        Initialize STT.
        
        Args:
            engine: STT engine to use
            model_size: Model size (tiny, base, small, medium, large)
            language: Language code
            device: "cpu" or "cuda"
        """
        self.engine_type = engine
        self.model_size = model_size
        self.language = language
        self.device = device
        
        self._recognizer = self._init_engine(engine)
        logger.info(f"STT initialized with {engine.value} ({model_size})")
    
    def _init_engine(self, engine: STTEngine) -> BaseSpeechRecognizer:
        """Initialize the specified engine."""
        if engine == STTEngine.FASTER_WHISPER:
            return FasterWhisperSTT(self.model_size, self.device, self.language)
        elif engine == STTEngine.WHISPER:
            return WhisperSTT(self.model_size, self.device, self.language)
        elif engine == STTEngine.WINDOWS:
            return WindowsSTT()
        else:
            raise ValueError(f"Unknown engine: {engine}")
    
    def transcribe(self, audio: bytes) -> TranscriptionResult:
        """
        Transcribe audio bytes.
        
        Args:
            audio: Audio bytes (WAV format)
            
        Returns:
            TranscriptionResult
        """
        return self._recognizer.transcribe(audio)
    
    def transcribe_file(self, path: Path) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            path: Path to audio file
            
        Returns:
            TranscriptionResult
        """
        return self._recognizer.transcribe_file(Path(path))
    
    async def transcribe_async(self, audio: bytes) -> TranscriptionResult:
        """Async transcription."""
        return await asyncio.to_thread(self.transcribe, audio)
    
    def transcribe_stream(self, audio_stream: Generator[bytes, None, None]) -> Generator[str, None, None]:
        """
        Transcribe streaming audio.
        
        Args:
            audio_stream: Generator yielding audio chunks
            
        Yields:
            Transcribed text chunks
        """
        # Accumulate audio and transcribe in chunks
        buffer = b""
        chunk_size = 16000 * 2 * 3  # 3 seconds of 16kHz mono audio
        
        for chunk in audio_stream:
            buffer += chunk
            
            if len(buffer) >= chunk_size:
                result = self.transcribe(buffer)
                buffer = b""
                
                if result.text.strip():
                    yield result.text


class FasterWhisperSTT(BaseSpeechRecognizer):
    """Faster Whisper STT engine (recommended)."""
    
    def __init__(self, model_size: str = "base", device: str = "cpu", language: str = "en"):
        self.model_size = model_size
        self.device = device
        self.language = language
        self._model = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                
                compute_type = "int8" if self.device == "cpu" else "float16"
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=compute_type,
                )
                logger.info(f"Loaded Faster Whisper model: {self.model_size}")
                
            except ImportError:
                raise ImportError("faster-whisper not installed. Run: pip install faster-whisper")
    
    def transcribe(self, audio: bytes) -> TranscriptionResult:
        """Transcribe audio bytes."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio)
            temp_path = Path(f.name)
        
        try:
            return self.transcribe_file(temp_path)
        finally:
            temp_path.unlink()
    
    def transcribe_file(self, path: Path) -> TranscriptionResult:
        """Transcribe an audio file."""
        self._load_model()
        
        segments, info = self._model.transcribe(
            str(path),
            language=self.language,
            vad_filter=True,
        )
        
        segment_list = []
        full_text = []
        
        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            })
            full_text.append(segment.text)
        
        return TranscriptionResult(
            text=" ".join(full_text).strip(),
            confidence=0.9,  # Whisper doesn't provide confidence
            language=info.language,
            segments=segment_list,
            duration=info.duration,
        )


class WhisperSTT(BaseSpeechRecognizer):
    """OpenAI Whisper STT engine."""
    
    def __init__(self, model_size: str = "base", device: str = "cpu", language: str = "en"):
        self.model_size = model_size
        self.device = device
        self.language = language
        self._model = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                import whisper
                
                self._model = whisper.load_model(self.model_size, device=self.device)
                logger.info(f"Loaded Whisper model: {self.model_size}")
                
            except ImportError:
                raise ImportError("openai-whisper not installed. Run: pip install openai-whisper")
    
    def transcribe(self, audio: bytes) -> TranscriptionResult:
        """Transcribe audio bytes."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio)
            temp_path = Path(f.name)
        
        try:
            return self.transcribe_file(temp_path)
        finally:
            temp_path.unlink()
    
    def transcribe_file(self, path: Path) -> TranscriptionResult:
        """Transcribe an audio file."""
        self._load_model()
        
        result = self._model.transcribe(
            str(path),
            language=self.language,
        )
        
        return TranscriptionResult(
            text=result["text"].strip(),
            confidence=0.9,
            language=result.get("language", self.language),
            segments=result.get("segments", []),
            duration=0,
        )


class WindowsSTT(BaseSpeechRecognizer):
    """Windows Speech Recognition (built-in)."""
    
    def __init__(self):
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
        except ImportError:
            raise ImportError("SpeechRecognition not installed. Run: pip install SpeechRecognition")
    
    def transcribe(self, audio: bytes) -> TranscriptionResult:
        """Transcribe audio bytes using Windows."""
        import speech_recognition as sr
        
        # Convert bytes to AudioData
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio)
            temp_path = f.name
        
        try:
            with sr.AudioFile(temp_path) as source:
                audio_data = self._recognizer.record(source)
            
            # Use Windows Speech Recognition
            text = self._recognizer.recognize_sphinx(audio_data)
            
            return TranscriptionResult(
                text=text,
                confidence=0.7,
                language="en",
                segments=[],
                duration=0,
            )
        finally:
            Path(temp_path).unlink()
    
    def transcribe_file(self, path: Path) -> TranscriptionResult:
        """Transcribe an audio file."""
        with open(path, "rb") as f:
            return self.transcribe(f.read())


class AudioRecorder:
    """
    Real-time audio recording for speech input.
    
    Records from the default microphone with voice activity detection.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
    ):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        
        self._recording = False
        self._audio_queue: queue.Queue = queue.Queue()
    
    def start_recording(self) -> Generator[bytes, None, None]:
        """
        Start recording and yield audio chunks.
        
        Yields:
            Audio data chunks
        """
        try:
            import sounddevice as sd
            
            self._recording = True
            
            def callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                if self._recording:
                    self._audio_queue.put(bytes(indata))
            
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                callback=callback,
                blocksize=self.chunk_size,
            ):
                while self._recording:
                    try:
                        chunk = self._audio_queue.get(timeout=0.1)
                        yield chunk
                    except queue.Empty:
                        continue
                        
        except ImportError:
            raise ImportError("sounddevice not installed. Run: pip install sounddevice")
    
    def stop_recording(self):
        """Stop the current recording."""
        self._recording = False
    
    def record_for_duration(self, duration: float) -> bytes:
        """
        Record for a specific duration.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Recorded audio bytes (WAV format)
        """
        try:
            import sounddevice as sd
            import numpy as np
            
            frames = int(duration * self.sample_rate)
            recording = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()
            
            # Convert to WAV bytes
            return self._to_wav_bytes(recording)
            
        except ImportError:
            raise ImportError("sounddevice not installed. Run: pip install sounddevice")
    
    def _to_wav_bytes(self, audio_data) -> bytes:
        """Convert numpy array to WAV bytes."""
        import io
        import numpy as np
        
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        return buffer.getvalue()
