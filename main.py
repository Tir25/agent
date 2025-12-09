#!/usr/bin/env python3
"""
The Sovereign Desktop - Main Entry Point

Usage:
    python main.py              # Start with default settings
    python main.py --voice      # Start with voice mode
    python main.py --debug      # Start with debug logging
    python main.py --config PATH  # Use custom config file
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import LLMEngine, SemanticRouter, ContextManager
from actuators import WindowsController, AudioController
from perception import VisionProcessor, OCREngine
from interfaces import VoiceLoop, VoiceLoopConfig
from utils import setup_logging, load_config, get_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="The Sovereign Desktop - Local-first AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Start in text mode
    python main.py --voice            # Start with voice interaction
    python main.py --debug --voice    # Voice mode with debug logging
        """,
    )
    
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file",
    )
    
    parser.add_argument(
        "--voice", "-v",
        action="store_true",
        help="Enable voice interaction mode",
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging",
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without any UI (server mode)",
    )
    
    return parser.parse_args()


class SovereignDesktop:
    """
    Main application class for The Sovereign Desktop.
    
    Orchestrates all components and provides the main interaction loop.
    """
    
    def __init__(self, config_path: Path = None, debug: bool = False):
        """
        Initialize The Sovereign Desktop.
        
        Args:
            config_path: Path to config file
            debug: Enable debug mode
        """
        # Load configuration
        self.config = load_config(config_path)
        if debug:
            self.config.debug = True
            self.config.logging.level = "DEBUG"
        
        # Setup logging
        setup_logging(
            level=self.config.logging.level,
            log_file=self.config.logging.file,
            max_size_mb=self.config.logging.max_size_mb,
        )
        
        self.logger = get_logger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("  The Sovereign Desktop")
        self.logger.info("  Your AI, Your Machine, Your Rules.")
        self.logger.info("=" * 60)
        
        # Initialize core components
        self._init_core()
        
        # Initialize peripherals
        self._init_peripherals()
    
    def _init_core(self):
        """Initialize core components."""
        self.logger.info("Initializing core components...")
        
        # LLM Engine
        self.llm = LLMEngine(
            model=self.config.llm.model,
            host=self.config.llm.host,
            temperature=self.config.llm.temperature,
            context_length=self.config.llm.context_length,
        )
        
        # Context Manager
        data_dir = Path(self.config.data_dir)
        self.context = ContextManager(
            persistence_path=data_dir / "context.db",
        )
        
        # Semantic Router
        self.router = SemanticRouter(llm_engine=self.llm)
        
        # Register tools
        self._register_tools()
    
    def _init_peripherals(self):
        """Initialize peripheral components."""
        self.logger.info("Initializing peripherals...")
        
        # Windows Controller
        try:
            self.windows = WindowsController()
        except Exception as e:
            self.logger.warning(f"Windows controller unavailable: {e}")
            self.windows = None
        
        # Audio Controller
        try:
            self.audio = AudioController()
        except Exception as e:
            self.logger.warning(f"Audio controller unavailable: {e}")
            self.audio = None
        
        # Vision Processor
        try:
            self.vision = VisionProcessor(
                max_resolution=self.config.vision.max_resolution,
            )
        except Exception as e:
            self.logger.warning(f"Vision processor unavailable: {e}")
            self.vision = None
        
        # OCR Engine
        if self.config.vision.ocr_enabled:
            try:
                self.ocr = OCREngine(backend=self.config.vision.ocr_backend)
            except Exception as e:
                self.logger.warning(f"OCR engine unavailable: {e}")
                self.ocr = None
        else:
            self.ocr = None
    
    def _register_tools(self):
        """Register tools with the semantic router."""
        from core.semantic_router import IntentCategory
        
        # System control tools
        if self.windows:
            self.router.register_tool(
                name="open_application",
                description="Open/launch an application",
                handler=lambda app: self.windows.launch_application(app),
                category=IntentCategory.SYSTEM_CONTROL,
            )
            
            self.router.register_tool(
                name="type_text",
                description="Type text using keyboard",
                handler=lambda text: self.windows.type_text(text),
                category=IntentCategory.SYSTEM_CONTROL,
            )
        
        # Audio tools
        if self.audio:
            self.router.register_tool(
                name="set_volume",
                description="Set system volume",
                handler=lambda level: self.audio.set_volume(float(level)),
                category=IntentCategory.MEDIA_CONTROL,
            )
            
            self.router.register_tool(
                name="play_pause",
                description="Toggle media playback",
                handler=lambda: self.audio.media_play_pause(),
                category=IntentCategory.MEDIA_CONTROL,
            )
    
    def process_command(self, text: str) -> str:
        """
        Process a command and return the response.
        
        Args:
            text: User command/query
            
        Returns:
            Response text
        """
        # Add to context
        self.context.add_message("user", text)
        
        try:
            # Parse and execute
            response = self.router.execute(text, context={
                "messages": self.context.get_messages_for_llm(limit=10),
                "screen": self.context.get_screen_context(),
            })
            
            # Add response to context
            self.context.add_message("assistant", str(response))
            
            return str(response)
            
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            return f"I encountered an error: {e}"
    
    def run_text_mode(self):
        """Run in text interaction mode."""
        self.logger.info("Starting text mode. Type 'quit' to exit.")
        print("\n🏛️ The Sovereign Desktop")
        print("Type your commands below. Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ("quit", "exit", "bye"):
                    print("Goodbye!")
                    break
                
                response = self.process_command(user_input)
                print(f"AI: {response}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                self.logger.error(f"Error: {e}")
                print(f"Error: {e}")
    
    def run_voice_mode(self):
        """Run in voice interaction mode."""
        self.logger.info("Starting voice mode...")
        
        voice_config = VoiceLoopConfig(
            stt_engine=self.config.voice.stt_engine,
            stt_model=self.config.voice.stt_model,
            tts_engine=self.config.voice.tts_engine,
            tts_voice=self.config.voice.tts_voice,
            wake_word=self.config.voice.wake_word,
            push_to_talk_key=self.config.voice.push_to_talk_key,
            language=self.config.voice.language,
        )
        
        voice_loop = VoiceLoop(
            config=voice_config,
            command_handler=self.process_command,
        )
        
        # Set up callbacks
        voice_loop.on_transcription(lambda t: print(f"You: {t}"))
        voice_loop.on_response(lambda r: print(f"AI: {r}"))
        
        print("\n🏛️ The Sovereign Desktop - Voice Mode")
        print(f"Press {voice_config.push_to_talk_key} to speak. Ctrl+C to exit.\n")
        
        try:
            with voice_loop:
                # Keep running until interrupted
                while True:
                    pass
        except KeyboardInterrupt:
            print("\nGoodbye!")
    
    def check_dependencies(self) -> bool:
        """Check if all required components are available."""
        issues = []
        
        # Check Ollama
        if not self.llm.is_available():
            issues.append(f"Ollama not running or model '{self.config.llm.model}' not available")
        
        # Report issues
        if issues:
            self.logger.warning("Dependency issues found:")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
            return False
        
        return True


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Initialize the application
        app = SovereignDesktop(
            config_path=args.config,
            debug=args.debug,
        )
        
        # Check dependencies
        if not app.check_dependencies():
            print("\n⚠️ Some dependencies are not available.")
            print("The agent may have limited functionality.")
            print("Make sure Ollama is running with the required model.\n")
        
        # Run in appropriate mode
        if args.voice:
            app.run_voice_mode()
        else:
            app.run_text_mode()
            
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
