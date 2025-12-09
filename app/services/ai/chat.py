"""
Chat Tool - General Conversation Service

Provides conversational responses using the local LLM.
Designed for concise, spoken responses.

Dependencies:
    - ollama: Python client for Ollama API

Model:
    - llama3.2:3b (fast, efficient for conversation)

Usage:
    from app.services.ai.chat import ChatTool
    
    tool = ChatTool()
    result = tool.execute(query="What is Python?")
    print(result.data["response"])
"""

from typing import Any, Dict

from app.interfaces.tool import BaseTool


class ChatTool(BaseTool):
    """
    General conversation tool using local LLM.
    
    Generates helpful, concise responses suitable for
    spoken output (TTS).
    
    Attributes:
        name: Tool identifier ("general_chat").
        description: Human-readable description for LLM routing.
        model: Ollama model name (default: llama3.2:3b).
        
    Example:
        tool = ChatTool()
        result = tool.execute(query="What is a car?")
        
        if result.success:
            print(result.data["response"])
    """
    
    SYSTEM_PROMPT = """You are a helpful, concise Windows Desktop Assistant. 
You are concise because your output is spoken aloud. 
Do not use markdown formatting like bold or lists, just plain text.
Keep responses brief and conversational - ideally 1-3 sentences."""
    
    def __init__(self, model: str = "llama3.2:3b"):
        """
        Initialize the ChatTool.
        
        Args:
            model: Ollama model name for conversation.
        """
        self.model = model
    
    @property
    def name(self) -> str:
        """Tool name for registry."""
        return "general_chat"
    
    @property
    def description(self) -> str:
        """Tool description for LLM routing."""
        return "Generates a conversational response. Params: query (str)."
    
    def _run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a conversational response.
        
        Args:
            query: The user's question or message.
            **kwargs: Additional options (temperature, etc.)
        
        Returns:
            Dictionary with:
            - response: The generated text response
            - model: Model name used
        """
        try:
            # Lazy import to avoid loading ollama if not used
            import ollama
            
            # Get optional parameters
            temperature = kwargs.get("temperature", 0.7)
            
            # Call Ollama for conversation
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                options={
                    "temperature": temperature,
                }
            )
            
            # Extract the response content
            response_text = response["message"]["content"]
            
            return {
                "response": response_text,
                "model": self.model,
            }
            
        except Exception as e:
            # If model is offline or any error occurs
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                return {
                    "response": "I cannot think right now. Please make sure Ollama is running.",
                    "model": self.model,
                    "error": error_msg,
                }
            raise  # Re-raise for other errors to be caught by safety wrapper


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing ChatTool...")
    
    tool = ChatTool()
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Model: {tool.model}")
    
    # Test questions
    test_queries = [
        "What is a car?",
        "How do I make coffee?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = tool.execute(query=query)
        
        if result.success:
            print(f"Response: {result.data['response']}")
        else:
            print(f"Failed: {result.error}")
