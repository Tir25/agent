"""
Voice Loop - Continuous Voice Interaction

Manages the continuous voice interaction loop combining:
- Speech recognition (STT)
- Intent processing
- Response generation
- Speech synthesis (TTS)
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional
import time

from .stt import SpeechToText, STTEngine, AudioRecorder
from .tts import TextToSpeech, TTSEngine

logger = logging.getLogger(__name__)


class VoiceLoopState(Enum):
    """Voice loop states."""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    PAUSED = auto()


@dataclass
class VoiceLoopConfig:
    """Configuration for the voice loop."""
    # STT settings
    stt_engine: STTEngine = STTEngine.FASTER_WHISPER
    stt_model: str = "base"
    language: str = "en"
    
    # TTS settings
    tts_engine: TTSEngine = TTSEngine.SAPI
    tts_voice: Optional[str] = None
    tts_rate: float = 1.0
    
    # Voice activation
    wake_word: Optional[str] = None
    push_to_talk: bool = True
    push_to_talk_key: str = "ctrl+space"
    
    # Timing
    silence_timeout: float = 2.0  # Seconds of silence to stop listening
    max_listen_time: float = 30.0  # Maximum listening time
    
    # Behavior
    confirm_before_action: bool = False
    speak_confirmations: bool = True
    beep_on_listen: bool = True


class VoiceLoop:
    """
    Manages continuous voice interaction.
    
    Provides a seamless voice interface combining speech recognition,
    command processing, and speech synthesis.
    """
    
    def __init__(
        self,
        config: VoiceLoopConfig = None,
        command_handler: Callable[[str], str] = None,
    ):
        """
        Initialize the voice loop.
        
        Args:
            config: Voice loop configuration
            command_handler: Function to process commands and return responses
        """
        self.config = config or VoiceLoopConfig()
        self.command_handler = command_handler or self._default_handler
        
        self._state = VoiceLoopState.IDLE
        self._running = False
        self._loop_thread: Optional[threading.Thread] = None
        
        # Initialize components
        self._stt = SpeechToText(
            engine=self.config.stt_engine,
            model_size=self.config.stt_model,
            language=self.config.language,
        )
        
        self._tts = TextToSpeech(
            engine=self.config.tts_engine,
            voice_id=self.config.tts_voice,
            rate=self.config.tts_rate,
        )
        
        self._recorder = AudioRecorder()
        
        # Callbacks
        self._on_state_change: list[Callable[[VoiceLoopState], None]] = []
        self._on_transcription: list[Callable[[str], None]] = []
        self._on_response: list[Callable[[str], None]] = []
        
        logger.info("Voice Loop initialized")
    
    @property
    def state(self) -> VoiceLoopState:
        """Get the current state."""
        return self._state
    
    def _set_state(self, state: VoiceLoopState):
        """Set state and notify listeners."""
        self._state = state
        for callback in self._on_state_change:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")
    
    def on_state_change(self, callback: Callable[[VoiceLoopState], None]):
        """Register a state change callback."""
        self._on_state_change.append(callback)
    
    def on_transcription(self, callback: Callable[[str], None]):
        """Register a transcription callback."""
        self._on_transcription.append(callback)
    
    def on_response(self, callback: Callable[[str], None]):
        """Register a response callback."""
        self._on_response.append(callback)
    
    def start(self):
        """Start the voice loop in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        logger.info("Voice loop started")
    
    def stop(self):
        """Stop the voice loop."""
        self._running = False
        self._set_state(VoiceLoopState.IDLE)
        
        if self._loop_thread:
            self._loop_thread.join(timeout=2.0)
        
        logger.info("Voice loop stopped")
    
    def pause(self):
        """Pause the voice loop."""
        self._set_state(VoiceLoopState.PAUSED)
    
    def resume(self):
        """Resume the voice loop."""
        if self._state == VoiceLoopState.PAUSED:
            self._set_state(VoiceLoopState.IDLE)
    
    def _run_loop(self):
        """Main voice loop."""
        while self._running:
            try:
                if self._state == VoiceLoopState.PAUSED:
                    time.sleep(0.1)
                    continue
                
                # Wait for activation
                if self.config.push_to_talk:
                    self._wait_for_push_to_talk()
                elif self.config.wake_word:
                    self._wait_for_wake_word()
                else:
                    # Always listening mode
                    pass
                
                if not self._running:
                    break
                
                # Listen for command
                self._set_state(VoiceLoopState.LISTENING)
                audio = self._listen()
                
                if not audio:
                    self._set_state(VoiceLoopState.IDLE)
                    continue
                
                # Transcribe
                self._set_state(VoiceLoopState.PROCESSING)
                result = self._stt.transcribe(audio)
                text = result.text.strip()
                
                if not text:
                    self._set_state(VoiceLoopState.IDLE)
                    continue
                
                # Notify transcription listeners
                for callback in self._on_transcription:
                    try:
                        callback(text)
                    except Exception as e:
                        logger.error(f"Transcription callback error: {e}")
                
                logger.info(f"Heard: {text}")
                
                # Process command
                response = self.command_handler(text)
                
                # Notify response listeners
                for callback in self._on_response:
                    try:
                        callback(response)
                    except Exception as e:
                        logger.error(f"Response callback error: {e}")
                
                # Speak response
                if response and self.config.speak_confirmations:
                    self._set_state(VoiceLoopState.SPEAKING)
                    self._speak(response)
                
                self._set_state(VoiceLoopState.IDLE)
                
            except Exception as e:
                logger.error(f"Voice loop error: {e}")
                self._set_state(VoiceLoopState.IDLE)
                time.sleep(0.5)
    
    def _wait_for_push_to_talk(self):
        """Wait for push-to-talk key."""
        from perception.listeners import HotkeyManager
        
        activated = threading.Event()
        
        def on_hotkey():
            activated.set()
        
        with HotkeyManager() as hotkey:
            hotkey.register(self.config.push_to_talk_key, on_hotkey)
            
            while self._running and not activated.is_set():
                activated.wait(timeout=0.1)
    
    def _wait_for_wake_word(self):
        """Wait for wake word detection."""
        # Simple implementation: continuously transcribe short chunks
        # and check for wake word
        while self._running:
            audio = self._recorder.record_for_duration(2.0)
            result = self._stt.transcribe(audio)
            
            if self.config.wake_word.lower() in result.text.lower():
                if self.config.beep_on_listen:
                    self._play_beep()
                return
    
    def _listen(self) -> Optional[bytes]:
        """Listen for voice input."""
        if self.config.beep_on_listen:
            self._play_beep()
        
        # Record with timeout
        audio = self._recorder.record_for_duration(self.config.max_listen_time)
        return audio
    
    def _speak(self, text: str):
        """Speak text."""
        self._tts.speak_and_play(text)
    
    def _play_beep(self):
        """Play a listening indicator beep."""
        try:
            import winsound
            winsound.Beep(800, 150)
        except Exception:
            pass
    
    def _default_handler(self, text: str) -> str:
        """Default command handler (echo)."""
        return f"I heard: {text}"
    
    # ==================== Manual Control ====================
    
    def listen_once(self) -> Optional[str]:
        """
        Listen for a single command and return the transcription.
        
        Returns:
            Transcribed text or None
        """
        self._set_state(VoiceLoopState.LISTENING)
        audio = self._listen()
        
        if audio:
            self._set_state(VoiceLoopState.PROCESSING)
            result = self._stt.transcribe(audio)
            self._set_state(VoiceLoopState.IDLE)
            return result.text.strip()
        
        self._set_state(VoiceLoopState.IDLE)
        return None
    
    def speak_response(self, text: str):
        """
        Speak a response.
        
        Args:
            text: Text to speak
        """
        self._set_state(VoiceLoopState.SPEAKING)
        self._speak(text)
        self._set_state(VoiceLoopState.IDLE)
    
    def process_text(self, text: str) -> str:
        """
        Process text as if it were spoken.
        
        Args:
            text: Text to process
            
        Returns:
            Response from command handler
        """
        return self.command_handler(text)
    
    # ==================== Context Manager ====================
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
