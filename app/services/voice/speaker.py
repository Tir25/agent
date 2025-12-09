"""
Text-to-Speech Speaker - Voice Output Service

Single-responsibility module for text-to-speech output using pyttsx3.
This service is fully isolated with error handling to prevent audio driver
crashes from killing the agent.

Dependencies:
    - pyttsx3: Text-to-speech conversion library

Usage:
    from app.services.voice.speaker import TextToSpeech
    
    speaker = TextToSpeech()
    speaker.speak("Hello, I am your assistant")
"""

from typing import Optional


class TextToSpeech:
    """
    Text-to-Speech service for voice output.
    
    Uses pyttsx3 for cross-platform speech synthesis with safety
    wrappers to prevent audio driver crashes.
    
    Attributes:
        rate: Speech rate in words per minute (default: 150).
        volume: Volume level 0.0-1.0 (default: 1.0).
        
    Example:
        speaker = TextToSpeech()
        speaker.speak("Hello World")
        
        # Custom settings
        speaker = TextToSpeech(rate=180, volume=0.8)
        speaker.speak("Faster speech")
    """
    
    def __init__(
        self, 
        rate: int = 150, 
        volume: float = 1.0,
        voice_id: Optional[str] = None
    ) -> None:
        """
        Initialize the TextToSpeech engine.
        
        Args:
            rate: Speech rate in words per minute.
            volume: Volume level from 0.0 to 1.0.
            voice_id: Optional specific voice ID to use.
        """
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self._engine = None
        self._initialized = False
    
    def _init_engine(self) -> bool:
        """
        Lazy-initialize the pyttsx3 engine.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        if self._initialized:
            return self._engine is not None
        
        try:
            import pyttsx3
            
            self._engine = pyttsx3.init()
            
            # Set properties
            self._engine.setProperty('rate', self.rate)
            self._engine.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice_id:
                self._engine.setProperty('voice', self.voice_id)
            
            self._initialized = True
            return True
            
        except ImportError:
            print("[Speaker] pyttsx3 not installed. Run: pip install pyttsx3")
            self._initialized = True
            return False
            
        except Exception as e:
            print(f"[Speaker] Failed to initialize TTS engine: {e}")
            self._initialized = True
            return False
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text.
        
        Args:
            text: The text to speak.
            
        Returns:
            True if speech completed successfully, False otherwise.
        """
        if not text or not text.strip():
            return True  # Nothing to speak
        
        if not self._init_engine():
            print(f"[Speaker] Cannot speak (engine not available): {text}")
            return False
        
        try:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
            
        except RuntimeError as e:
            # Common error: engine already running
            print(f"[Speaker] Runtime error (retrying): {e}")
            try:
                self._engine.stop()
                self._engine.say(text)
                self._engine.runAndWait()
                return True
            except Exception:
                return False
            
        except Exception as e:
            # Catch all other errors to prevent crashes
            print(f"[Speaker] Error during speech: {e}")
            return False
    
    def stop(self) -> None:
        """Stop any ongoing speech."""
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
    
    def set_rate(self, rate: int) -> None:
        """
        Set the speech rate.
        
        Args:
            rate: Words per minute (typically 100-200).
        """
        self.rate = rate
        if self._engine:
            try:
                self._engine.setProperty('rate', rate)
            except Exception:
                pass
    
    def set_volume(self, volume: float) -> None:
        """
        Set the speech volume.
        
        Args:
            volume: Volume level from 0.0 to 1.0.
        """
        self.volume = max(0.0, min(1.0, volume))
        if self._engine:
            try:
                self._engine.setProperty('volume', self.volume)
            except Exception:
                pass
    
    def get_voices(self) -> list:
        """
        Get list of available voices.
        
        Returns:
            List of voice objects with id, name, languages.
        """
        if not self._init_engine():
            return []
        
        try:
            return self._engine.getProperty('voices')
        except Exception:
            return []


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing TextToSpeech...")
    
    speaker = TextToSpeech(rate=150)
    print(f"Voices available: {len(speaker.get_voices())}")
    
    success = speaker.speak("Hello, I am your Sovereign Desktop Assistant.")
    print(f"Speech result: {'Success' if success else 'Failed'}")
