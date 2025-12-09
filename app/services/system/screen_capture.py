"""
Screen Capture Tool - Visual Perception Service

Captures screenshots of the primary monitor for visual analysis.
Uses mss for fast, cross-platform screen capture.

Dependencies:
    - mss: Fast cross-platform screenshots

Usage:
    from app.services.system.screen_capture import ScreenCaptureTool
    
    tool = ScreenCaptureTool()
    result = tool.execute()
    print(f"Screenshot saved to: {result.data['path']}")
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

from app.interfaces.tool import BaseTool


class ScreenCaptureTool(BaseTool):
    """
    Screen capture tool for taking screenshots.
    
    Captures the primary monitor and saves to a temporary file.
    The temporary file is kept alive for downstream processing
    (e.g., vision model analysis).
    
    Attributes:
        name: Tool identifier ("capture_screen").
        description: Human-readable description for LLM routing.
        
    Example:
        tool = ScreenCaptureTool()
        result = tool.execute()
        
        if result.success:
            image_path = result.data["path"]
            # Pass to vision model...
    """
    
    @property
    def name(self) -> str:
        """Tool name for registry."""
        return "capture_screen"
    
    @property
    def description(self) -> str:
        """Tool description for LLM routing."""
        return "Takes a screenshot of the primary monitor. Returns: path to the temporary image file."
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Capture the primary monitor screen.
        
        Args:
            **kwargs: Currently unused, but allows for future options
                      like monitor_index, region, etc.
        
        Returns:
            Dictionary with:
            - path: Absolute path to the saved screenshot
            - width: Image width in pixels
            - height: Image height in pixels
            - monitor: Monitor index captured
        """
        # Lazy import to avoid loading mss if not used
        import mss
        import mss.tools
        
        # Create a temporary file that persists (delete=False)
        # This ensures the file exists for downstream processes
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".png",
            prefix="sovereign_screen_",
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()  # Close so mss can write to it
        
        # Capture the screen
        with mss.mss() as sct:
            # Monitor index 1 is the primary monitor
            # (index 0 is a virtual monitor spanning all screens)
            monitor_index = kwargs.get("monitor", 1)
            
            # Ensure monitor exists
            if monitor_index >= len(sct.monitors):
                monitor_index = 1
            
            monitor = sct.monitors[monitor_index]
            
            # Capture the screen
            screenshot = sct.grab(monitor)
            
            # Save to the temporary file
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=temp_path)
            
            return {
                "path": temp_path,
                "width": screenshot.width,
                "height": screenshot.height,
                "monitor": monitor_index,
            }


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing ScreenCaptureTool...")
    
    tool = ScreenCaptureTool()
    print(f"Name: {tool.name}")
    print(f"Description: {tool.description}")
    
    result = tool.execute()
    
    if result.success:
        print(f"\n✓ Screenshot captured!")
        print(f"  Path: {result.data['path']}")
        print(f"  Size: {result.data['width']}x{result.data['height']}")
        print(f"  Monitor: {result.data['monitor']}")
        
        # Verify file exists
        from pathlib import Path
        if Path(result.data['path']).exists():
            size_kb = Path(result.data['path']).stat().st_size / 1024
            print(f"  File Size: {size_kb:.1f} KB")
    else:
        print(f"\n✗ Failed: {result.error}")
