"""
The Sovereign Desktop - Core Module

This module contains the brain of the agent:
- LLM Engine: Ollama/Llama integration
- Semantic Router: Intent classification and routing
- Context Manager: Memory and state management
- Intent Router: LLM-based intent classification
"""

from .llm_engine import LLMEngine
from .semantic_router import SemanticRouter
from .context_manager import ContextManager
from .router import (
    IntentRouter,
    IntentCategory,
    RouterResult,
    route_intent,
    route_intent_sync,
    get_router,
)

__all__ = [
    "LLMEngine",
    "SemanticRouter",
    "ContextManager",
    "IntentRouter",
    "IntentCategory",
    "RouterResult",
    "route_intent",
    "route_intent_sync",
    "get_router",
]
