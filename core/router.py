"""
Intent Router Module

Classifies user intents using a local LLM (llama3.2:3b via Ollama) and routes
requests to appropriate handlers.

The router uses a strict JSON output format to ensure reliable parsing
and falls back to GENERAL_CHAT if parsing fails.

Example:
    >>> from core.router import route_intent, IntentCategory
    >>> result = await route_intent("Set volume to 50%")
    >>> print(result)
    {'category': 'SYSTEM_CONTROL', 'action': 'set_volume', 'parameters': {'value': 50}}
"""

import asyncio
import json
import logging
import re
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class IntentCategory(str, Enum):
    """Categorization of user intents."""
    
    SYSTEM_CONTROL = "SYSTEM_CONTROL"    # Volume, brightness, power
    APP_CONTROL = "APP_CONTROL"          # Open/close applications
    OFFICE_WORK = "OFFICE_WORK"          # Word, Excel, document tasks
    BROWSER = "BROWSER"                  # Web navigation, search
    GENERAL_CHAT = "GENERAL_CHAT"        # Conversation, questions
    
    @classmethod
    def from_string(cls, value: str) -> "IntentCategory":
        """Convert string to IntentCategory with fallback."""
        value_upper = value.upper().replace(" ", "_").replace("-", "_")
        try:
            return cls(value_upper)
        except ValueError:
            # Try partial matching
            for category in cls:
                if category.value in value_upper or value_upper in category.value:
                    return category
            return cls.GENERAL_CHAT


@dataclass
class RouterResult:
    """Result from intent routing."""
    
    category: IntentCategory
    action: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    raw_query: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "action": self.action,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "raw_query": self.raw_query,
        }


# System prompt for intent classification
ROUTER_SYSTEM_PROMPT = """You are an intent classification AI. Your job is to analyze user queries and output a JSON object classifying the intent.

Available intent categories:
- SYSTEM_CONTROL: Volume control, brightness, mute, system power (shutdown, restart, sleep)
- APP_CONTROL: Opening, closing, focusing, or switching applications
- OFFICE_WORK: Microsoft Word, Excel, document creation, spreadsheet tasks
- BROWSER: Web browsing, searching, opening URLs, web automation
- GENERAL_CHAT: Questions, conversation, information requests, anything else

Output format (strict JSON only, no markdown, no explanation):
{
    "category": "<CATEGORY>",
    "action": "<specific_action>",
    "parameters": {<extracted_parameters>}
}

Examples:

User: "Set volume to 50%"
{"category": "SYSTEM_CONTROL", "action": "set_volume", "parameters": {"value": 50}}

User: "Open Chrome"
{"category": "APP_CONTROL", "action": "open_app", "parameters": {"app_name": "chrome"}}

User: "Create a Word document with title 'Meeting Notes'"
{"category": "OFFICE_WORK", "action": "create_document", "parameters": {"app": "word", "title": "Meeting Notes"}}

User: "Search for Python tutorials"
{"category": "BROWSER", "action": "search", "parameters": {"query": "Python tutorials"}}

User: "What's the weather like?"
{"category": "GENERAL_CHAT", "action": "question", "parameters": {"topic": "weather"}}

User: "Mute"
{"category": "SYSTEM_CONTROL", "action": "mute", "parameters": {}}

User: "Close Notepad"
{"category": "APP_CONTROL", "action": "close_app", "parameters": {"app_name": "notepad"}}

User: "Write 'Hello World' in cell A1"
{"category": "OFFICE_WORK", "action": "write_cell", "parameters": {"app": "excel", "cell": "A1", "value": "Hello World"}}

IMPORTANT: Output ONLY valid JSON. No markdown code blocks, no explanations, no extra text."""


class IntentRouter:
    """
    Routes user intents using a local LLM.
    
    Uses llama3.2:3b via Ollama for fast, local intent classification.
    """
    
    def __init__(
        self,
        model: str = "llama3.2:3b",
        ollama_host: str = "http://localhost:11434",
        temperature: float = 0.1,
    ):
        """
        Initialize the intent router.
        
        Args:
            model: Ollama model name for routing (smaller = faster).
            ollama_host: Ollama API host URL.
            temperature: LLM temperature (lower = more deterministic).
        """
        self.model = model
        self.ollama_host = ollama_host
        self.temperature = temperature
        self._llm = None
        
        logger.info(f"IntentRouter initialized with model: {model}")
    
    def _get_llm(self):
        """Lazy-load the LLM."""
        if self._llm is None:
            try:
                from langchain_ollama import ChatOllama
                self._llm = ChatOllama(
                    model=self.model,
                    base_url=self.ollama_host,
                    temperature=self.temperature,
                )
            except ImportError:
                logger.error("langchain-ollama not installed")
                raise
        return self._llm
    
    async def route_intent(self, user_query: str) -> RouterResult:
        """
        Classify user intent and extract parameters.
        
        Args:
            user_query: The user's input text.
            
        Returns:
            RouterResult with category, action, and parameters.
            
        Example:
            >>> router = IntentRouter()
            >>> result = await router.route_intent("Set volume to 50%")
            >>> print(result.category)
            IntentCategory.SYSTEM_CONTROL
        """
        try:
            llm = self._get_llm()
            
            # Build messages
            messages = [
                ("system", ROUTER_SYSTEM_PROMPT),
                ("human", user_query),
            ]
            
            # Invoke LLM
            response = await asyncio.to_thread(llm.invoke, messages)
            raw_response = response.content.strip()
            
            logger.debug(f"Router LLM response: {raw_response}")
            
            # Parse JSON response
            parsed = self._parse_json_response(raw_response)
            
            if parsed:
                category = IntentCategory.from_string(
                    parsed.get("category", "GENERAL_CHAT")
                )
                return RouterResult(
                    category=category,
                    action=parsed.get("action"),
                    parameters=parsed.get("parameters", {}),
                    confidence=1.0,
                    raw_query=user_query,
                )
            else:
                logger.warning(f"Failed to parse router response: {raw_response}")
                return self._fallback_result(user_query)
                
        except Exception as e:
            logger.error(f"Router error: {e}")
            return self._fallback_result(user_query)
    
    def route_intent_sync(self, user_query: str) -> RouterResult:
        """
        Synchronous version of route_intent.
        
        Args:
            user_query: The user's input text.
            
        Returns:
            RouterResult with category, action, and parameters.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context, use thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.route_intent(user_query)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.route_intent(user_query))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.route_intent(user_query))
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response with fallback strategies.
        
        Args:
            response: Raw LLM response text.
            
        Returns:
            Parsed dictionary or None.
        """
        # Clean up common issues
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            response = "\n".join(lines)
        
        # Try direct parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to find nested JSON (handles pretty-printed)
        try:
            # Find first { and last }
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = response[start:end + 1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _fallback_result(self, user_query: str) -> RouterResult:
        """
        Generate fallback result when LLM fails.
        
        Uses simple keyword matching as backup.
        """
        query_lower = user_query.lower()
        
        # Simple keyword-based fallback
        if any(kw in query_lower for kw in ["volume", "mute", "unmute", "brightness", "shutdown", "restart", "sleep"]):
            return RouterResult(
                category=IntentCategory.SYSTEM_CONTROL,
                action="unknown",
                parameters={},
                confidence=0.5,
                raw_query=user_query,
            )
        elif any(kw in query_lower for kw in ["open", "close", "launch", "start", "run", "focus"]):
            return RouterResult(
                category=IntentCategory.APP_CONTROL,
                action="unknown",
                parameters={},
                confidence=0.5,
                raw_query=user_query,
            )
        elif any(kw in query_lower for kw in ["word", "excel", "document", "spreadsheet", "cell"]):
            return RouterResult(
                category=IntentCategory.OFFICE_WORK,
                action="unknown",
                parameters={},
                confidence=0.5,
                raw_query=user_query,
            )
        elif any(kw in query_lower for kw in ["search", "google", "browse", "website", "url", "http"]):
            return RouterResult(
                category=IntentCategory.BROWSER,
                action="unknown",
                parameters={},
                confidence=0.5,
                raw_query=user_query,
            )
        else:
            return RouterResult(
                category=IntentCategory.GENERAL_CHAT,
                action="chat",
                parameters={},
                confidence=0.5,
                raw_query=user_query,
            )


# Global router instance
_router: Optional[IntentRouter] = None


def get_router() -> IntentRouter:
    """Get or create the global router instance."""
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router


async def route_intent(user_query: str) -> Dict[str, Any]:
    """
    Convenience function to route an intent.
    
    Args:
        user_query: The user's input text.
        
    Returns:
        Dictionary with category, action, and parameters.
        
    Example:
        >>> result = await route_intent("Set volume to 50%")
        >>> print(result)
        {'category': 'SYSTEM_CONTROL', 'action': 'set_volume', 'parameters': {'value': 50}}
    """
    router = get_router()
    result = await router.route_intent(user_query)
    return result.to_dict()


def route_intent_sync(user_query: str) -> Dict[str, Any]:
    """
    Synchronous convenience function to route an intent.
    
    Args:
        user_query: The user's input text.
        
    Returns:
        Dictionary with category, action, and parameters.
    """
    router = get_router()
    result = router.route_intent_sync(user_query)
    return result.to_dict()


# Action mappings for each category
ACTION_HANDLERS = {
    IntentCategory.SYSTEM_CONTROL: {
        "set_volume": "actuators.system_ops.AudioController.set_master_volume",
        "get_volume": "actuators.system_ops.AudioController.get_volume",
        "mute": "actuators.system_ops.AudioController.mute_master_volume",
        "unmute": "actuators.system_ops.AudioController.mute_master_volume",
        "set_brightness": "actuators.system_ops.set_brightness",
        "get_brightness": "actuators.system_ops.get_brightness",
    },
    IntentCategory.APP_CONTROL: {
        "open_app": "actuators.system_ops.launch_app",
        "close_app": "actuators.system_ops.close_app",
        "focus_app": "actuators.system_ops.focus_window",
    },
    IntentCategory.OFFICE_WORK: {
        "create_document": "actuators.office_ops.create_word_document",
        "append_text": "actuators.office_ops.append_text_to_doc",
        "read_document": "actuators.office_ops.read_word_document",
        "write_cell": "actuators.office_ops.write_excel_cell",
        "read_cells": "actuators.office_ops.read_excel_data",
    },
    IntentCategory.BROWSER: {
        "search": None,  # Requires browser agent
        "navigate": None,
        "click": None,
    },
    IntentCategory.GENERAL_CHAT: {
        "chat": None,  # Requires main LLM
        "question": None,
    },
}


def get_handler_for_intent(result: RouterResult) -> Optional[str]:
    """
    Get the handler function path for an intent result.
    
    Args:
        result: RouterResult from routing.
        
    Returns:
        Handler function path string or None.
    """
    category_handlers = ACTION_HANDLERS.get(result.category, {})
    if result.action:
        return category_handlers.get(result.action)
    return None
