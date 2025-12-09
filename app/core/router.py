"""
Semantic Router - Intelligence Layer for Tool Selection

This module provides the "Brain" that takes natural language user queries
and decides which registered tool to execute with what parameters.

Uses Ollama with llama3.2:3b for intent classification.

Usage:
    from app.core.router import SemanticRouter
    from app.core.registry import ToolRegistry
    
    registry = ToolRegistry()
    # ... register tools ...
    
    router = SemanticRouter(registry)
    result = router.route("Set volume to 50%")
    # {'tool_name': 'set_volume', 'parameters': {'level': 50}}
"""

import json
import re
from typing import Any, Dict, Optional

from app.core.registry import ToolRegistry
from app.utils.result import CommandResult


class SemanticRouter:
    """
    Intelligence layer that routes natural language commands to tools.
    
    Uses Ollama LLM to classify user intent and extract parameters,
    then maps to the appropriate registered tool.
    
    Attributes:
        registry: ToolRegistry instance containing available tools.
        model: Ollama model name to use for classification.
        
    Example:
        registry = ToolRegistry()
        registry.register_tool(VolumeTool())
        
        router = SemanticRouter(registry)
        result = router.route("Turn the volume up to 80")
        # {'tool_name': 'set_volume', 'parameters': {'level': 80}}
    """
    
    def __init__(
        self, 
        registry: ToolRegistry, 
        model: str = "llama3.2:3b"
    ) -> None:
        """
        Initialize the Semantic Router.
        
        Args:
            registry: ToolRegistry instance with registered tools.
            model: Ollama model name (default: llama3.2:3b).
        """
        self.registry = registry
        self.model = model
        self._ollama = None
    
    def _get_ollama(self) -> Any:
        """
        Lazy-load Ollama client.
        
        Returns:
            Ollama module if available.
            
        Raises:
            ImportError: If ollama is not installed.
        """
        if self._ollama is None:
            import ollama
            self._ollama = ollama
        return self._ollama
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with dynamically injected tool descriptions.
        
        Returns:
            System prompt string for the LLM.
        """
        tools_description = self.registry.list_tools()
        
        return f"""You are an intent classifier for a desktop automation assistant.

{tools_description}

Given the user query, analyze their intent and output a JSON object with:
- "tool_name": String that EXACTLY matches one of the available tool names above
- "parameters": Dictionary of arguments for that tool

If no tool matches the query (e.g., general questions, chitchat), use:
- "tool_name": "general_chat"
- "parameters": {{"message": "the user's message"}}

CRITICAL PARAMETER RULES:

FOR VOLUME (set_volume):
- To SET volume: use "level" parameter (0-100)
- To MUTE: use "mute": true
- To UNMUTE: use "mute": false  
- To GET current volume: use "action": "get"

FOR BRIGHTNESS (set_brightness):
- To SET brightness: use "level" parameter (0-100)
- To GET current brightness: use "action": "get"

FOR APP LAUNCHER (launch_app):
- Use "app_name" parameter with the application name

FOR WORD (write_word_doc):
- Use "text" parameter with the content to write
- Optionally use "filename" for the file path

FOR EXCEL (read_excel):
- Use "filename" parameter for the file path
- Use "range" parameter for the cell range (e.g., "A1:B10")

EXAMPLES:
- "Set volume to 50" → {{"tool_name": "set_volume", "parameters": {{"level": 50}}}}
- "Mute the audio" → {{"tool_name": "set_volume", "parameters": {{"mute": true}}}}
- "Unmute sound" → {{"tool_name": "set_volume", "parameters": {{"mute": false}}}}
- "What's the current volume?" → {{"tool_name": "set_volume", "parameters": {{"action": "get"}}}}
- "Get current brightness level" → {{"tool_name": "set_brightness", "parameters": {{"action": "get"}}}}
- "Set brightness to 80" → {{"tool_name": "set_brightness", "parameters": {{"level": 80}}}}
- "Open Chrome" → {{"tool_name": "launch_app", "parameters": {{"app_name": "chrome"}}}}
- "Write hello world in Word" → {{"tool_name": "write_word_doc", "parameters": {{"text": "hello world"}}}}
- "Read data.xlsx range A1:B10" → {{"tool_name": "read_excel", "parameters": {{"filename": "data.xlsx", "range": "A1:B10"}}}}
- "What's the weather?" → {{"tool_name": "general_chat", "parameters": {{"message": "What's the weather?"}}}}

Output ONLY the JSON object, no explanations or markdown."""
    
    def _clean_json_response(self, response: str) -> str:
        """
        Clean LLM response to extract valid JSON.
        
        Handles common issues like:
        - Markdown code blocks (```json ... ```)
        - Extra whitespace
        - Trailing text
        
        Args:
            response: Raw LLM response string.
            
        Returns:
            Cleaned JSON string.
        """
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Strip whitespace
        response = response.strip()
        
        # Try to find JSON object boundaries
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            response = response[start:end + 1]
        
        return response
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into a dictionary.
        
        Args:
            response: Raw LLM response.
            
        Returns:
            Parsed dictionary with tool_name and parameters.
        """
        cleaned = self._clean_json_response(response)
        
        try:
            result = json.loads(cleaned)
            
            # Validate structure
            if "tool_name" not in result:
                result["tool_name"] = "general_chat"
            if "parameters" not in result:
                result["parameters"] = {}
            
            return result
            
        except json.JSONDecodeError:
            # Fallback for unparseable responses
            return {
                "tool_name": "general_chat",
                "parameters": {"message": response, "parse_error": True}
            }
    
    def route(self, user_query: str) -> Dict[str, Any]:
        """
        Route a user query to the appropriate tool.
        
        Args:
            user_query: Natural language command from the user.
            
        Returns:
            Dictionary with:
            - tool_name: Name of the tool to execute
            - parameters: Arguments for the tool
            - error: (optional) Error message if routing failed
        """
        if not user_query or not user_query.strip():
            return {
                "tool_name": "general_chat",
                "parameters": {"message": ""},
                "error": "Empty query"
            }
        
        try:
            ollama = self._get_ollama()
        except ImportError:
            return {
                "tool_name": "general_chat",
                "parameters": {"message": user_query},
                "error": "Ollama not installed. Run: pip install ollama"
            }
        
        # Build the system prompt with available tools
        system_prompt = self._build_system_prompt()
        
        try:
            # Call Ollama for intent classification
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                options={
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "num_predict": 256   # Limit response length
                }
            )
            
            # Extract the response content
            llm_response = response["message"]["content"]
            
            # Parse the JSON response
            result = self._parse_response(llm_response)
            
            # Validate tool exists
            if result["tool_name"] != "general_chat":
                if result["tool_name"] not in self.registry:
                    result["warning"] = f"Tool '{result['tool_name']}' not found in registry"
            
            return result
            
        except Exception as e:
            return {
                "tool_name": "general_chat",
                "parameters": {"message": user_query},
                "error": f"Routing error: {str(e)}"
            }
    
    def route_and_execute(self, user_query: str) -> CommandResult:
        """
        Route a query and immediately execute the matched tool.
        
        Args:
            user_query: Natural language command.
            
        Returns:
            CommandResult from the tool execution.
        """
        route_result = self.route(user_query)
        
        tool_name = route_result.get("tool_name")
        parameters = route_result.get("parameters", {})
        
        # Handle routing errors
        if "error" in route_result:
            return CommandResult(
                success=False,
                error=route_result["error"],
                data=route_result
            )
        
        # Handle general chat (no tool)
        if tool_name == "general_chat":
            return CommandResult(
                success=True,
                data={
                    "type": "chat",
                    "message": parameters.get("message", user_query)
                }
            )
        
        # Get and execute the tool
        tool = self.registry.get_tool(tool_name)
        
        if tool is None:
            return CommandResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                data=route_result
            )
        
        # Execute the tool with extracted parameters
        return tool.execute(**parameters)


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SEMANTIC ROUTER VERIFICATION")
    print("=" * 60)
    
    from app.services.system.volume import VolumeTool
    from app.services.system.brightness import BrightnessTool
    from app.services.system.launcher import AppLauncherTool
    from app.services.office.word import WordWriterTool
    from app.services.office.excel import ExcelReaderTool
    
    # Create registry and register tools
    registry = ToolRegistry()
    registry.register_tool(VolumeTool())
    registry.register_tool(BrightnessTool())
    registry.register_tool(AppLauncherTool())
    registry.register_tool(WordWriterTool())
    registry.register_tool(ExcelReaderTool())
    
    print(f"\nRegistry: {registry}")
    
    # Create router
    router = SemanticRouter(registry)
    print(f"Router model: {router.model}")
    
    # Test queries
    test_queries = [
        "Set the volume to 60 percent",
        "Open notepad",
        "What time is it?",
        "Turn brightness to 80",
    ]
    
    print("\n" + "-" * 60)
    print("TESTING ROUTES")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = router.route(query)
        print(f"  → Tool: {result.get('tool_name')}")
        print(f"  → Params: {result.get('parameters')}")
        if "error" in result:
            print(f"  → Error: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
