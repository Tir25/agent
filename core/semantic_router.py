"""
Semantic Router - Intent Classification and Tool Routing

This module analyzes user input to determine intent and routes
to the appropriate tool/action handler.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """High-level intent categories."""
    SYSTEM_CONTROL = auto()      # OS-level operations
    BROWSER_ACTION = auto()      # Web browsing tasks
    FILE_OPERATION = auto()      # File management
    APPLICATION_CONTROL = auto()  # App launching/control
    MEDIA_CONTROL = auto()       # Audio/video control
    INFORMATION_QUERY = auto()   # Questions/search
    CONVERSATION = auto()        # General chat
    VISION_QUERY = auto()        # Screen understanding
    UNKNOWN = auto()


@dataclass
class Intent:
    """Parsed intent with metadata."""
    category: IntentCategory
    action: str
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    raw_query: str = ""


@dataclass
class ToolDefinition:
    """Definition of a registered tool."""
    name: str
    description: str
    handler: Callable
    triggers: list[str] = field(default_factory=list)
    category: IntentCategory = IntentCategory.UNKNOWN
    parameters_schema: Optional[dict] = None


class SemanticRouter:
    """
    Semantic Router for intent classification and tool routing.
    
    Uses LLM for understanding complex queries and pattern matching
    for common commands. Routes to registered tools based on intent.
    """
    
    def __init__(self, llm_engine=None):
        """
        Initialize the Semantic Router.
        
        Args:
            llm_engine: Optional LLMEngine instance for complex routing
        """
        self.llm_engine = llm_engine
        self._tools: dict[str, ToolDefinition] = {}
        self._pattern_matchers: list[tuple[re.Pattern, IntentCategory, str]] = []
        
        self._register_default_patterns()
        logger.info("Semantic Router initialized")
    
    def _register_default_patterns(self):
        """Register default pattern matchers for common commands."""
        patterns = [
            # System control
            (r"(open|launch|start|run)\s+(.+)", IntentCategory.SYSTEM_CONTROL, "open_application"),
            (r"(close|exit|quit|kill)\s+(.+)", IntentCategory.SYSTEM_CONTROL, "close_application"),
            (r"(shutdown|restart|sleep|lock)\s*(computer|pc)?", IntentCategory.SYSTEM_CONTROL, "system_power"),
            
            # File operations
            (r"(create|make|new)\s+(file|folder|directory)\s+(.+)", IntentCategory.FILE_OPERATION, "create_item"),
            (r"(delete|remove)\s+(file|folder|directory)?\s*(.+)", IntentCategory.FILE_OPERATION, "delete_item"),
            (r"(move|copy)\s+(.+)\s+to\s+(.+)", IntentCategory.FILE_OPERATION, "transfer_item"),
            
            # Browser actions
            (r"(go to|open|visit|browse)\s+(https?://\S+|www\.\S+|\S+\.(com|org|net|io))", IntentCategory.BROWSER_ACTION, "navigate"),
            (r"search\s+(for|about)?\s*(.+)", IntentCategory.BROWSER_ACTION, "search"),
            
            # Media control
            (r"(play|pause|stop|resume)\s*(music|video|media)?", IntentCategory.MEDIA_CONTROL, "playback"),
            (r"(volume|sound)\s*(up|down|mute|unmute|\d+%?)", IntentCategory.MEDIA_CONTROL, "volume"),
            (r"(next|previous|skip)\s*(track|song)?", IntentCategory.MEDIA_CONTROL, "track_control"),
            
            # Vision queries
            (r"(what('s| is)|describe|read|look at)\s*(on\s*)?(the\s*)?(screen|display|this)", IntentCategory.VISION_QUERY, "describe_screen"),
            (r"(find|locate|where('s| is))\s+(.+)\s*(on\s*(the\s*)?(screen|display))?", IntentCategory.VISION_QUERY, "find_element"),
        ]
        
        for pattern, category, action in patterns:
            self._pattern_matchers.append((re.compile(pattern, re.IGNORECASE), category, action))
    
    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable,
        triggers: Optional[list[str]] = None,
        category: IntentCategory = IntentCategory.UNKNOWN,
        parameters_schema: Optional[dict] = None,
    ) -> None:
        """
        Register a tool with the router.
        
        Args:
            name: Unique tool name
            description: Human-readable description
            handler: Callable to execute the tool
            triggers: List of trigger phrases
            category: Intent category
            parameters_schema: JSON schema for parameters
        """
        tool = ToolDefinition(
            name=name,
            description=description,
            handler=handler,
            triggers=triggers or [],
            category=category,
            parameters_schema=parameters_schema,
        )
        self._tools[name] = tool
        logger.info(f"Registered tool: {name}")
    
    def parse_intent(self, query: str, context: Optional[dict] = None) -> Intent:
        """
        Parse user query to extract intent.
        
        Args:
            query: User's natural language query
            context: Optional context from previous interactions
            
        Returns:
            Parsed Intent object
        """
        query = query.strip()
        
        # Try pattern matching first (fast path)
        for pattern, category, action in self._pattern_matchers:
            if match := pattern.search(query):
                return Intent(
                    category=category,
                    action=action,
                    parameters={"groups": match.groups()},
                    confidence=0.9,
                    raw_query=query,
                )
        
        # Use LLM for complex intent parsing
        if self.llm_engine:
            return self._llm_parse_intent(query, context)
        
        # Fallback to conversation
        return Intent(
            category=IntentCategory.CONVERSATION,
            action="chat",
            confidence=0.5,
            raw_query=query,
        )
    
    def _llm_parse_intent(self, query: str, context: Optional[dict] = None) -> Intent:
        """Use LLM to parse complex intents."""
        tools_description = "\n".join(
            f"- {t.name}: {t.description}" for t in self._tools.values()
        )
        
        system_prompt = f"""You are an intent classifier for a desktop automation agent.
Analyze the user's query and respond with JSON containing:
- category: one of [SYSTEM_CONTROL, BROWSER_ACTION, FILE_OPERATION, APPLICATION_CONTROL, MEDIA_CONTROL, INFORMATION_QUERY, CONVERSATION, VISION_QUERY]
- action: specific action to take
- parameters: relevant parameters extracted from the query
- confidence: 0.0 to 1.0

Available tools:
{tools_description}

Respond ONLY with valid JSON, no explanation."""

        try:
            response = self.llm_engine.generate(
                prompt=query,
                system_prompt=system_prompt,
            )
            
            # Parse JSON from response
            data = json.loads(response.content)
            
            return Intent(
                category=IntentCategory[data.get("category", "UNKNOWN")],
                action=data.get("action", "unknown"),
                parameters=data.get("parameters", {}),
                confidence=float(data.get("confidence", 0.5)),
                raw_query=query,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"LLM intent parsing failed: {e}")
            return Intent(
                category=IntentCategory.CONVERSATION,
                action="chat",
                confidence=0.3,
                raw_query=query,
            )
    
    def route(self, intent: Intent) -> tuple[Optional[ToolDefinition], dict]:
        """
        Route intent to appropriate tool.
        
        Args:
            intent: Parsed intent
            
        Returns:
            Tuple of (tool or None, processed parameters)
        """
        # Direct action match
        for tool in self._tools.values():
            if tool.name == intent.action:
                return tool, intent.parameters
        
        # Category-based matching
        category_tools = [t for t in self._tools.values() if t.category == intent.category]
        if category_tools:
            # Return first matching tool (could be improved with scoring)
            return category_tools[0], intent.parameters
        
        return None, intent.parameters
    
    def execute(self, query: str, context: Optional[dict] = None) -> Any:
        """
        Parse, route, and execute a query.
        
        Args:
            query: User's natural language query
            context: Optional context
            
        Returns:
            Tool execution result or chat response
        """
        intent = self.parse_intent(query, context)
        logger.info(f"Parsed intent: {intent.category.name} -> {intent.action}")
        
        tool, params = self.route(intent)
        
        if tool:
            logger.info(f"Executing tool: {tool.name}")
            try:
                return tool.handler(**params)
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                raise
        else:
            # Fallback to LLM conversation
            if self.llm_engine:
                response = self.llm_engine.generate(query)
                return response.content
            return "I'm not sure how to help with that."


# Decorator for easy tool registration
def register_tool(
    name: str,
    description: str,
    triggers: Optional[list[str]] = None,
    category: IntentCategory = IntentCategory.UNKNOWN,
):
    """Decorator to register a function as a tool."""
    def decorator(func: Callable) -> Callable:
        func._tool_metadata = {
            "name": name,
            "description": description,
            "triggers": triggers or [],
            "category": category,
        }
        return func
    return decorator
