"""
Vision Tool - AI Image Analysis Service

Wrapper around Ollama's llama3.2-vision model for image analysis.
Takes an image path and a question, returns the model's answer.

Dependencies:
    - ollama: Python client for Ollama API

Model:
    - llama3.2-vision (must be pulled: ollama pull llama3.2-vision)

Usage:
    from app.services.ai.vision import VisionTool
    
    tool = VisionTool()
    result = tool.execute(image_path="/path/to/image.png", query="What is in this image?")
    print(result.data["response"])
"""

from typing import Any, Dict

from app.interfaces.tool import BaseTool


class VisionTool(BaseTool):
    """
    Vision Language Model tool for image analysis.
    
    Uses Ollama's llama3.2-vision model to analyze images
    and answer questions about their contents.
    
    Attributes:
        name: Tool identifier ("analyze_image").
        description: Human-readable description for LLM routing.
        model: Ollama model name (default: llama3.2-vision).
        
    Example:
        tool = VisionTool()
        result = tool.execute(
            image_path="screenshot.png",
            query="What application is open in this screenshot?"
        )
        
        if result.success:
            print(result.data["response"])
    """
    
    def __init__(self, model: str = "llama3.2-vision"):
        """
        Initialize the VisionTool.
        
        Args:
            model: Ollama model name for vision analysis.
        """
        self.model = model
    
    @property
    def name(self) -> str:
        """Tool name for registry."""
        return "analyze_image"
    
    @property
    def description(self) -> str:
        """Tool description for LLM routing."""
        return "Analyzes an image using a Vision Language Model. Params: image_path (str), query (str)."
    
    def _run(self, image_path: str, query: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze an image using the vision model.
        
        Args:
            image_path: Path to the image file to analyze.
            query: Question or prompt about the image.
            **kwargs: Additional options (temperature, etc.)
        
        Returns:
            Dictionary with:
            - response: The model's text response
            - model: Model name used
            - image_path: Path to analyzed image
        """
        # Lazy import to avoid loading ollama if not used
        import ollama
        import base64
        from pathlib import Path
        
        # Get optional parameters
        temperature = kwargs.get("temperature", 0.7)
        
        # Read image file and encode as base64
        # Ollama requires base64 encoded images
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Call Ollama with the vision model
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": query,
                    "images": [image_data]
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
            "image_path": image_path,
        }


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing VisionTool...")
    print("Note: Requires llama3.2-vision model to be pulled in Ollama.")
    
    tool = VisionTool()
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Model: {tool.model}")
    
    # To test, first capture a screenshot
    from app.services.system.screen_capture import ScreenCaptureTool
    
    capture = ScreenCaptureTool()
    capture_result = capture.execute()
    
    if capture_result.success:
        image_path = capture_result.data["path"]
        print(f"\nCaptured screenshot: {image_path}")
        
        print("\nAnalyzing screenshot...")
        result = tool.execute(
            image_path=image_path,
            query="Describe what you see in this screenshot in 2-3 sentences."
        )
        
        if result.success:
            print(f"\n✓ Analysis complete!")
            print(f"Response: {result.data['response']}")
        else:
            print(f"\n✗ Failed: {result.error}")
    else:
        print(f"\n✗ Screenshot failed: {capture_result.error}")
