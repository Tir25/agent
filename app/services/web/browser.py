"""
Browser Tool - Web Automation Service

Autonomous web browsing using the browser-use library.
Uses llama3.2-vision for visual understanding of web pages.

Dependencies:
    - browser-use: Autonomous browser agent
    - langchain-ollama: LLM integration
    - playwright: Browser automation

Setup:
    pip install browser-use langchain-ollama
    playwright install

Usage:
    from app.services.web.browser import BrowserTool
    
    tool = BrowserTool()
    result = tool.execute(task_description="Search for Python tutorials")
"""

import asyncio
from typing import Any, Dict

from app.interfaces.tool import BaseTool


class BrowserTool(BaseTool):
    """
    Autonomous web browsing tool using browser-use.
    
    Uses llama3.2-vision for visual understanding to navigate
    web pages and complete tasks autonomously.
    
    Attributes:
        name: Tool identifier ("browse_web").
        description: Human-readable description for LLM routing.
        model: Ollama model name (default: llama3.2-vision).
        headless: Whether to run browser in headless mode.
        
    Example:
        tool = BrowserTool()
        result = tool.execute(
            task_description="Search Google for weather in New York"
        )
        
        if result.success:
            print(result.data["result"])
    """
    
    def __init__(self, model: str = "llama3.2-vision", headless: bool = False):
        """
        Initialize the BrowserTool.
        
        Args:
            model: Ollama model name for vision-based browsing.
            headless: If False, browser window is visible.
        """
        self.model = model
        self.headless = headless
    
    @property
    def name(self) -> str:
        """Tool name for registry."""
        return "browse_web"
    
    @property
    def description(self) -> str:
        """Tool description for LLM routing."""
        return "Performs autonomous web browsing to find information or execute tasks. Params: task_description (str)."
    
    def _run(self, task_description: str, **kwargs) -> Dict[str, Any]:
        """
        Execute an autonomous web browsing task.
        
        Args:
            task_description: Natural language description of what to do.
            **kwargs: Additional options.
        
        Returns:
            Dictionary with:
            - result: The final result from the browser agent
            - task: The original task description
            - steps: Number of steps taken
        """
        try:
            # Lazy imports to avoid loading heavy libs if not used
            from browser_use import Agent, Browser, BrowserConfig
            from langchain_ollama import ChatOllama
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            return {
                "result": f"Missing dependency: {missing}. Please install with: pip install browser-use langchain-ollama",
                "task": task_description,
                "error": str(e),
            }
        
        async def run_browser_task():
            """Async function to run the browser agent."""
            # Initialize the LLM with vision capabilities
            llm = ChatOllama(
                model=self.model,
                temperature=0.0,  # Deterministic for browsing
            )
            
            # Initialize the browser
            browser_config = BrowserConfig(headless=self.headless)
            browser = Browser(config=browser_config)
            
            try:
                # Create and run the agent
                agent = Agent(
                    task=task_description,
                    llm=llm,
                    browser=browser,
                )
                
                # Execute the task
                result = await agent.run()
                
                # Extract the final result
                if hasattr(result, 'final_result'):
                    final_result = result.final_result
                elif hasattr(result, 'history') and result.history:
                    # Get the last meaningful result from history
                    final_result = str(result.history[-1]) if result.history else "Task completed"
                else:
                    final_result = str(result)
                
                steps = len(result.history) if hasattr(result, 'history') else 0
                
                return {
                    "result": final_result,
                    "task": task_description,
                    "steps": steps,
                }
                
            finally:
                # Clean up browser
                await browser.close()
        
        # Run the async task in a new event loop
        try:
            result = asyncio.run(run_browser_task())
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for common Playwright errors
            if "playwright" in error_msg.lower() or "browser" in error_msg.lower():
                if "executable" in error_msg.lower() or "install" in error_msg.lower():
                    return {
                        "result": "Playwright browsers not installed. Please run: playwright install",
                        "task": task_description,
                        "error": error_msg,
                    }
            
            # Generic error
            return {
                "result": f"Browser automation failed: {error_msg}",
                "task": task_description,
                "error": error_msg,
            }


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing BrowserTool...")
    print("Note: Requires browser-use and playwright to be installed.")
    
    tool = BrowserTool()
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Model: {tool.model}")
    print(f"Headless: {tool.headless}")
    
    # Simple test - search Google
    print("\nExecuting test task...")
    result = tool.execute(
        task_description="Go to google.com and search for 'Python programming'"
    )
    
    if result.success:
        print(f"\n✓ Task completed!")
        print(f"Result: {result.data.get('result', 'No result')[:200]}...")
        print(f"Steps: {result.data.get('steps', 'Unknown')}")
    else:
        print(f"\n✗ Failed: {result.error}")
