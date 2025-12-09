#!/usr/bin/env python3
"""
The Sovereign Desktop - Main Entry Point

This is the ONLY file you run. It bootstraps the Registry, Router,
and Voice services and enters the interaction loop.

Usage:
    python main.py              # Start in text mode
    python main.py --voice      # Start with voice mode
    python main.py --debug      # Start with debug logging

Your AI, Your Machine, Your Rules.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# =============================================================================
# IMPORTS - All from our modular architecture
# =============================================================================

# Core infrastructure
from app.core.registry import ToolRegistry
from app.core.router import SemanticRouter
from app.utils.result import CommandResult

# System control tools
from app.services.system.volume import VolumeTool
from app.services.system.brightness import BrightnessTool
from app.services.system.launcher import AppLauncherTool

# Office tools
from app.services.office.word import WordWriterTool
from app.services.office.excel import ExcelReaderTool

# Vision tools
from app.services.system.screen_capture import ScreenCaptureTool
from app.services.ai.vision import VisionTool

# Voice I/O
from app.services.voice.speaker import TextToSpeech
from app.services.voice.listener import VoiceListener


# =============================================================================
# CONFIGURATION
# =============================================================================

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
        "--voice", "-v",
        action="store_true",
        help="Enable voice interaction mode",
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging",
    )
    
    return parser.parse_args()


# =============================================================================
# THE SOVEREIGN DESKTOP AGENT
# =============================================================================

class SovereignAgent:
    """
    The Sovereign Desktop Agent.
    
    Orchestrates all components:
    - ToolRegistry: Central place for all tools
    - SemanticRouter: LLM-based intent classification
    - VoiceListener: Speech-to-text (ears)
    - TextToSpeech: Text-to-speech (mouth)
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize The Sovereign Desktop Agent.
        
        Args:
            debug: Enable debug mode with verbose logging.
        """
        self.debug = debug
        
        # Initialize components
        self._init_registry()
        self._init_router()
        self._init_voice()
        
        print("\n" + "=" * 60)
        print("  🏛️  THE SOVEREIGN DESKTOP")
        print("  Your AI, Your Machine, Your Rules.")
        print("=" * 60)
        print(f"\n  Tools Registered: {len(self.registry)}")
        print(f"  Router Model: {self.router.model}")
        print()
    
    def _init_registry(self):
        """Initialize and populate the tool registry."""
        self.registry = ToolRegistry()
        
        # Register System Control tools
        self.registry.register_tool(VolumeTool())
        self.registry.register_tool(BrightnessTool())
        self.registry.register_tool(AppLauncherTool())
        
        # Register Office tools
        self.registry.register_tool(WordWriterTool())
        self.registry.register_tool(ExcelReaderTool())
        
        # Register Vision tools
        self.registry.register_tool(ScreenCaptureTool())
        self.registry.register_tool(VisionTool())
        
        if self.debug:
            print("[DEBUG] Registry initialized:")
            print(self.registry.list_tools())
    
    def _init_router(self):
        """Initialize the semantic router."""
        self.router = SemanticRouter(self.registry)
        
        if self.debug:
            print(f"[DEBUG] Router initialized with model: {self.router.model}")
    
    def _init_voice(self):
        """Initialize voice I/O components."""
        self.mouth = TextToSpeech(rate=150)
        self.ears = VoiceListener()
        
        if self.debug:
            print(f"[DEBUG] Voice components initialized")
            print(f"[DEBUG] TTS voices available: {len(self.mouth.get_voices())}")
    
    def speak(self, text: str):
        """Speak text aloud."""
        if self.debug:
            print(f"[SPEAK] {text}")
        self.mouth.speak(text)
    
    def process_command(self, user_query: str) -> str:
        """
        Process a user command through the full pipeline.
        
        1. Route the query (LLM classification)
        2. Execute the matched tool
        3. Return the response
        
        Args:
            user_query: Natural language command from user.
            
        Returns:
            Response string for the user.
        """
        if self.debug:
            print(f"\n[DEBUG] Processing: '{user_query}'")
        
        # Step 1: Route the command
        decision = self.router.route(user_query)
        
        tool_name = decision.get("tool_name")
        parameters = decision.get("parameters", {})
        
        if self.debug:
            print(f"[DEBUG] Routed to: {tool_name}")
            print(f"[DEBUG] Parameters: {parameters}")
        
        # Step 2: Handle routing errors
        if "error" in decision:
            return f"I had trouble understanding that: {decision['error']}"
        
        # Step 3: Handle general chat (no tool needed)
        if tool_name == "general_chat":
            return self._handle_chat(user_query)
        
        # Step 3.5: Handle visual queries (screen analysis)
        if tool_name == "visual_query":
            return self._handle_visual_query(parameters)
        
        # Step 4: Execute the tool
        tool = self.registry.get_tool(tool_name)
        
        if tool is None:
            return f"I don't have a tool called '{tool_name}'"
        
        result: CommandResult = tool.execute(**parameters)
        
        # Step 5: Format the response
        if result.success:
            return self._format_success(tool_name, result.data)
        else:
            return f"Sorry, that didn't work: {result.error}"
    
    def _handle_chat(self, query: str) -> str:
        """Handle general chat (non-tool) queries."""
        # For now, return a simple response
        # In the future, this would call the LLM for a conversational response
        return "I'm your desktop assistant. I can control volume, brightness, launch apps, analyze your screen, and work with Office documents. How can I help?"
    
    def _handle_visual_query(self, parameters: dict) -> str:
        """
        Handle visual queries (screen analysis).
        
        Two-step process:
        1. Capture screenshot
        2. Analyze with vision model
        3. Cleanup temp file
        
        Args:
            parameters: Dict with 'query' key containing the user's question.
            
        Returns:
            Vision model's response string.
        """
        user_query = parameters.get("query", "Describe what you see on the screen.")
        
        if self.debug:
            print("[DEBUG] Visual query - capturing screen...")
        
        # Step 1: Capture Screen
        screen_tool = self.registry.get_tool("capture_screen")
        if screen_tool is None:
            return "Screen capture tool not available."
        
        screen_result = screen_tool.execute()
        
        if not screen_result.success:
            return f"I couldn't capture the screen: {screen_result.error}"
        
        image_path = screen_result.data["path"]
        
        if self.debug:
            print(f"[DEBUG] Screenshot saved: {image_path}")
            print(f"[DEBUG] Analyzing with vision model...")
        
        # Step 2: Analyze Image
        vision_tool = self.registry.get_tool("analyze_image")
        if vision_tool is None:
            return "Vision analysis tool not available."
        
        vision_result = vision_tool.execute(
            image_path=image_path,
            query=user_query
        )
        
        # Step 3: Cleanup temp file
        try:
            os.remove(image_path)
            if self.debug:
                print(f"[DEBUG] Cleaned up temp file: {image_path}")
        except Exception:
            pass  # Ignore cleanup errors
        
        # Return result
        if vision_result.success:
            return vision_result.data["response"]
        else:
            return f"I couldn't analyze the image: {vision_result.error}"

    
    def _format_success(self, tool_name: str, data: dict) -> str:
        """Format a success response for the user."""
        if tool_name == "set_volume":
            if "volume" in data:
                return f"Volume set to {data['volume']}%"
            elif "muted" in data:
                return "Audio muted" if data["muted"] else "Audio unmuted"
        
        elif tool_name == "set_brightness":
            if "brightness" in data:
                return f"Brightness set to {data['brightness']}%"
        
        elif tool_name == "launch_app":
            return f"Launched {data.get('app', 'the application')}"
        
        elif tool_name == "write_word_doc":
            if data.get("saved"):
                return f"Created Word document: {data.get('filename', 'document')}"
            else:
                return "Created Word document. Use File > Save to save it."
        
        elif tool_name == "read_excel":
            rows = data.get("rows", 0)
            cols = data.get("cols", 0)
            return f"Read {rows} rows and {cols} columns from Excel"
        
        return f"Done: {data}"
    
    # =========================================================================
    # INTERACTION MODES
    # =========================================================================
    
    def run_text_mode(self):
        """Run in text interaction mode."""
        print("📝 Text Mode - Type your commands. Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ("quit", "exit", "bye", "q"):
                    print("Goodbye!")
                    break
                
                response = self.process_command(user_input)
                print(f"AI: {response}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                if self.debug:
                    import traceback
                    traceback.print_exc()
                print(f"Error: {e}")
    
    def run_voice_mode(self):
        """Run in voice interaction mode."""
        print("🎤 Voice Mode - Speak your commands. Press Ctrl+C to exit.\n")
        
        # Initialize the listener
        if not self.ears.initialize():
            print("❌ Failed to initialize voice listener.")
            print("   Make sure you have a microphone and the Vosk model installed.")
            return
        
        self.speak("Sovereign Desktop is ready. How can I help you?")
        
        try:
            while True:
                # Listen for user speech
                print("Listening...", end="\r")
                user_text = self.ears.listen(timeout_chunks=50)
                
                if not user_text:
                    continue
                
                print(f"You: {user_text}")
                
                # Check for exit commands
                if user_text.lower() in ("quit", "exit", "goodbye", "stop"):
                    self.speak("Goodbye!")
                    break
                
                # Process and respond
                response = self.process_command(user_text)
                print(f"AI: {response}")
                self.speak(response)
                
        except KeyboardInterrupt:
            print("\n")
            self.speak("Goodbye!")
        finally:
            self.ears.close()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Initialize the agent
        agent = SovereignAgent(debug=args.debug)
        
        # Run in appropriate mode
        if args.voice:
            agent.run_voice_mode()
        else:
            agent.run_text_mode()
            
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
