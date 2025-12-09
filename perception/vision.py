"""
Vision Processing - Screen Capture and Image Processing

Handles screen capture, image preprocessing, and vision-related
utilities for the multimodal LLM.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy imports for optional dependencies
mss = None
PIL_Image = None


def _ensure_mss():
    global mss
    if mss is None:
        import mss as _mss
        mss = _mss


def _ensure_pil():
    global PIL_Image
    if PIL_Image is None:
        from PIL import Image
        PIL_Image = Image


@dataclass
class CaptureRegion:
    """Defines a screen region to capture."""
    left: int
    top: int
    width: int
    height: int
    
    def to_dict(self) -> dict:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class Screenshot:
    """Captured screenshot with metadata."""
    image_bytes: bytes
    width: int
    height: int
    timestamp: datetime
    region: Optional[CaptureRegion] = None
    monitor_index: int = 0
    
    def save(self, path: Path) -> Path:
        """Save screenshot to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(self.image_bytes)
        return path
    
    def to_base64(self) -> str:
        """Convert to base64 string."""
        import base64
        return base64.b64encode(self.image_bytes).decode("utf-8")


class ScreenCapture:
    """
    High-performance screen capture using MSS.
    
    Supports full screen and region-based capture with
    multiple monitor support.
    """
    
    def __init__(self):
        """Initialize the screen capture."""
        _ensure_mss()
        self._sct = mss.mss()
        logger.info("Screen capture initialized")
    
    @property
    def monitors(self) -> list[dict]:
        """Get list of available monitors."""
        return self._sct.monitors
    
    @property
    def primary_monitor(self) -> dict:
        """Get the primary monitor info."""
        # monitors[0] is the combined virtual screen, monitors[1] is primary
        return self._sct.monitors[1] if len(self._sct.monitors) > 1 else self._sct.monitors[0]
    
    def capture_full(self, monitor_index: int = 1) -> Screenshot:
        """
        Capture the full screen of a monitor.
        
        Args:
            monitor_index: Monitor to capture (1 = primary, 0 = all)
            
        Returns:
            Screenshot object
        """
        monitor = self._sct.monitors[monitor_index]
        return self._capture_region(monitor, monitor_index)
    
    def capture_region(self, region: CaptureRegion) -> Screenshot:
        """
        Capture a specific screen region.
        
        Args:
            region: Region to capture
            
        Returns:
            Screenshot object
        """
        return self._capture_region(region.to_dict(), region=region)
    
    def capture_window(self, hwnd: int) -> Optional[Screenshot]:
        """
        Capture a specific window by handle.
        
        Args:
            hwnd: Window handle
            
        Returns:
            Screenshot object or None if window not found
        """
        try:
            import win32gui
            import win32con
            
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            region = CaptureRegion(
                left=rect[0],
                top=rect[1],
                width=rect[2] - rect[0],
                height=rect[3] - rect[1],
            )
            return self.capture_region(region)
        except Exception as e:
            logger.error(f"Failed to capture window: {e}")
            return None
    
    def _capture_region(
        self,
        monitor_dict: dict,
        monitor_index: int = 0,
        region: Optional[CaptureRegion] = None,
    ) -> Screenshot:
        """Internal capture method."""
        sct_img = self._sct.grab(monitor_dict)
        
        # Convert to PNG bytes
        _ensure_pil()
        img = PIL_Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        image_bytes = buffer.getvalue()
        
        return Screenshot(
            image_bytes=image_bytes,
            width=sct_img.width,
            height=sct_img.height,
            timestamp=datetime.now(),
            region=region,
            monitor_index=monitor_index,
        )
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, "_sct"):
            self._sct.close()


class VisionProcessor:
    """
    Processes screenshots for LLM vision input.
    
    Includes preprocessing, resizing, and optimization
    for efficient multimodal inference.
    """
    
    def __init__(
        self,
        max_resolution: Tuple[int, int] = (1920, 1080),
        quality: int = 85,
    ):
        """
        Initialize the vision processor.
        
        Args:
            max_resolution: Maximum output resolution (width, height)
            quality: JPEG quality for compression (1-100)
        """
        self.max_resolution = max_resolution
        self.quality = quality
        self._capture = ScreenCapture()
        
        logger.info(f"Vision processor initialized (max: {max_resolution})")
    
    def capture_and_process(
        self,
        region: Optional[CaptureRegion] = None,
        resize: bool = True,
    ) -> bytes:
        """
        Capture and process a screenshot for LLM input.
        
        Args:
            region: Optional region to capture
            resize: Whether to resize to max_resolution
            
        Returns:
            Processed image bytes (JPEG)
        """
        if region:
            screenshot = self._capture.capture_region(region)
        else:
            screenshot = self._capture.capture_full()
        
        return self.process_image(screenshot.image_bytes, resize)
    
    def process_image(self, image_bytes: bytes, resize: bool = True) -> bytes:
        """
        Process an image for LLM input.
        
        Args:
            image_bytes: Raw image bytes
            resize: Whether to resize
            
        Returns:
            Processed image bytes (JPEG)
        """
        _ensure_pil()
        
        img = PIL_Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize if needed
        if resize:
            img.thumbnail(self.max_resolution, PIL_Image.Resampling.LANCZOS)
        
        # Compress to JPEG
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
        
        return buffer.getvalue()
    
    def get_screen_for_llm(self) -> bytes:
        """Convenience method to get ready-for-LLM screenshot."""
        return self.capture_and_process()
    
    def annotate_regions(
        self,
        image_bytes: bytes,
        regions: list[Tuple[int, int, int, int]],
        labels: Optional[list[str]] = None,
    ) -> bytes:
        """
        Annotate image with bounding boxes.
        
        Args:
            image_bytes: Source image
            regions: List of (x, y, width, height) tuples
            labels: Optional labels for each region
            
        Returns:
            Annotated image bytes
        """
        _ensure_pil()
        from PIL import ImageDraw, ImageFont
        
        img = PIL_Image.open(BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)
        
        # Try to get a font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font = ImageFont.load_default()
        
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
        
        for i, (x, y, w, h) in enumerate(regions):
            color = colors[i % len(colors)]
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            
            if labels and i < len(labels):
                draw.text((x, y - 20), labels[i], fill=color, font=font)
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
