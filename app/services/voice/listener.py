"""
Voice Listener - Speech-to-Text Service

Single-responsibility module for speech recognition using Vosk.
Handles microphone input with graceful error recovery for disconnects.

Dependencies:
    - vosk: Offline speech recognition
    - pyaudio: Audio input handling

Model:
    Download from: https://alphacephei.com/vosk/models
    Default: model/vosk-model-small-en-us-0.15

Usage:
    from app.services.voice.listener import VoiceListener
    
    listener = VoiceListener()
    text = listener.listen()
    print(f"You said: {text}")
"""

import json
from pathlib import Path
from typing import Optional, Any


class VoiceListener:
    """
    Voice Listener service for speech-to-text.
    
    Uses Vosk for offline speech recognition with PyAudio for
    microphone input. Handles IOError gracefully by attempting
    to restart the stream.
    
    Attributes:
        model_path: Path to the Vosk model directory.
        sample_rate: Audio sample rate (default: 16000).
        
    Example:
        listener = VoiceListener()
        
        while True:
            text = listener.listen()
            if text:
                print(f"You said: {text}")
    """
    
    def __init__(
        self,
        model_path: str = "model/vosk-model-small-en-us-0.15",
        sample_rate: int = 16000,
        chunk_size: int = 4096
    ) -> None:
        """
        Initialize the VoiceListener.
        
        Args:
            model_path: Path to the Vosk model directory.
            sample_rate: Audio sample rate in Hz.
            chunk_size: Bytes to read per audio chunk.
        """
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        self._model: Any = None
        self._recognizer: Any = None
        self._audio: Any = None
        self._stream: Any = None
        self._initialized = False
    
    def _init_vosk(self) -> bool:
        """
        Lazy-initialize Vosk model and recognizer.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        if self._model is not None:
            return True
        
        try:
            from vosk import Model, KaldiRecognizer
            
            # Check if model exists
            model_dir = Path(self.model_path)
            if not model_dir.exists():
                print(f"[Listener] Model not found at: {self.model_path}")
                print("[Listener] Download from: https://alphacephei.com/vosk/models")
                return False
            
            self._model = Model(str(model_dir))
            self._recognizer = KaldiRecognizer(self._model, self.sample_rate)
            
            return True
            
        except ImportError:
            print("[Listener] Vosk not installed. Run: pip install vosk")
            return False
            
        except Exception as e:
            print(f"[Listener] Failed to load Vosk model: {e}")
            return False
    
    def _init_audio_stream(self) -> bool:
        """
        Initialize PyAudio stream.
        
        Returns:
            True if stream created successfully, False otherwise.
        """
        try:
            import pyaudio
            
            if self._audio is None:
                self._audio = pyaudio.PyAudio()
            
            # Close existing stream if any
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception:
                    pass
            
            # Open new stream
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            return True
            
        except ImportError:
            print("[Listener] PyAudio not installed. Run: pip install pyaudio")
            return False
            
        except IOError as e:
            print(f"[Listener] Microphone error: {e}")
            return False
            
        except Exception as e:
            print(f"[Listener] Failed to open audio stream: {e}")
            return False
    
    def _restart_stream(self) -> bool:
        """
        Attempt to restart the audio stream after an error.
        
        Returns:
            True if restart successful, False otherwise.
        """
        print("[Listener] Attempting to restart audio stream...")
        
        # Close existing stream
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        
        # Reinitialize
        return self._init_audio_stream()
    
    def initialize(self) -> bool:
        """
        Initialize the listener (model and audio stream).
        
        Returns:
            True if initialization successful, False otherwise.
        """
        if self._initialized:
            return True
        
        if not self._init_vosk():
            return False
        
        if not self._init_audio_stream():
            return False
        
        self._initialized = True
        return True
    
    def listen(self, timeout_chunks: int = 50) -> Optional[str]:
        """
        Listen for speech and return recognized text.
        
        Args:
            timeout_chunks: Number of chunks to read before returning
                           (to prevent blocking forever).
        
        Returns:
            Recognized text string, or None if no speech detected.
        """
        if not self.initialize():
            return None
        
        try:
            chunks_read = 0
            
            while chunks_read < timeout_chunks:
                try:
                    data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                    chunks_read += 1
                    
                except IOError as e:
                    # Microphone disconnect - try to restart
                    print(f"[Listener] IOError: {e}")
                    if not self._restart_stream():
                        return None
                    continue
                
                # Process audio with Vosk
                if self._recognizer.AcceptWaveform(data):
                    result = self._recognizer.Result()
                    
                    # Parse JSON result
                    try:
                        result_dict = json.loads(result)
                        text = result_dict.get("text", "").strip()
                        
                        if text:
                            return text
                            
                    except json.JSONDecodeError:
                        continue
            
            # Check partial result at end
            partial = self._recognizer.PartialResult()
            try:
                partial_dict = json.loads(partial)
                text = partial_dict.get("partial", "").strip()
                return text if text else None
            except json.JSONDecodeError:
                return None
                
        except Exception as e:
            print(f"[Listener] Error during listen: {e}")
            return None
    
    def listen_continuous(self):
        """
        Generator that yields recognized text continuously.
        
        Yields:
            Recognized text strings as they are detected.
        """
        if not self.initialize():
            return
        
        while True:
            try:
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                
            except IOError as e:
                print(f"[Listener] IOError: {e}")
                if not self._restart_stream():
                    return
                continue
            
            if self._recognizer.AcceptWaveform(data):
                result = self._recognizer.Result()
                
                try:
                    result_dict = json.loads(result)
                    text = result_dict.get("text", "").strip()
                    
                    if text:
                        yield text
                        
                except json.JSONDecodeError:
                    continue
    
    def close(self) -> None:
        """Clean up audio resources."""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing VoiceListener...")
    print("Note: Requires Vosk model to be downloaded.")
    
    listener = VoiceListener()
    
    if listener.initialize():
        print("Listener initialized. Speak something...")
        text = listener.listen(timeout_chunks=100)
        print(f"Recognized: {text}")
        listener.close()
    else:
        print("Failed to initialize listener.")
