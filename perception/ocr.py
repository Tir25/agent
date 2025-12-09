"""
OCR Engine - Text Extraction from Screen

Uses Tesseract or EasyOCR for extracting text from screenshots.
Supports both quick recognition and detailed element detection.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Single OCR detection result."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    
    def __str__(self):
        return f"{self.text} ({self.confidence:.2f})"


@dataclass
class OCROutput:
    """Complete OCR output from an image."""
    full_text: str
    results: List[OCRResult]
    language: str
    processing_time: float


class OCREngine:
    """
    OCR Engine supporting multiple backends.
    
    Backends:
    - tesseract: Fast, lightweight (requires Tesseract installed)
    - easyocr: More accurate, supports more languages (GPU optional)
    """
    
    def __init__(
        self,
        backend: str = "tesseract",
        languages: List[str] = None,
        use_gpu: bool = False,
    ):
        """
        Initialize the OCR engine.
        
        Args:
            backend: OCR backend ("tesseract" or "easyocr")
            languages: Languages to detect (default: ["en"])
            use_gpu: Use GPU acceleration (easyocr only)
        """
        self.backend = backend
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        
        self._reader = None
        self._init_backend()
        
        logger.info(f"OCR Engine initialized (backend: {backend})")
    
    def _init_backend(self):
        """Initialize the selected backend."""
        if self.backend == "tesseract":
            try:
                import pytesseract
                self._pytesseract = pytesseract
            except ImportError:
                raise ImportError("pytesseract not installed. Run: pip install pytesseract")
        
        elif self.backend == "easyocr":
            try:
                import easyocr
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.use_gpu,
                    verbose=False,
                )
            except ImportError:
                raise ImportError("easyocr not installed. Run: pip install easyocr")
        
        else:
            raise ValueError(f"Unknown OCR backend: {self.backend}")
    
    def extract_text(self, image: bytes) -> str:
        """
        Extract plain text from an image.
        
        Args:
            image: Image bytes (PNG, JPEG, etc.)
            
        Returns:
            Extracted text as a string
        """
        result = self.process(image)
        return result.full_text
    
    def process(self, image: bytes) -> OCROutput:
        """
        Process an image and return detailed OCR results.
        
        Args:
            image: Image bytes
            
        Returns:
            OCROutput with full text and individual detections
        """
        import time
        from io import BytesIO
        from PIL import Image
        
        start_time = time.time()
        img = Image.open(BytesIO(image))
        
        if self.backend == "tesseract":
            result = self._process_tesseract(img)
        else:
            result = self._process_easyocr(image)
        
        result.processing_time = time.time() - start_time
        return result
    
    def _process_tesseract(self, img) -> OCROutput:
        """Process with Tesseract."""
        import pytesseract
        
        # Get detailed data
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        results = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])
            
            if text and conf > 0:
                results.append(OCRResult(
                    text=text,
                    confidence=conf / 100.0,
                    bbox=(
                        data["left"][i],
                        data["top"][i],
                        data["width"][i],
                        data["height"][i],
                    ),
                ))
        
        full_text = pytesseract.image_to_string(img)
        
        return OCROutput(
            full_text=full_text.strip(),
            results=results,
            language="+".join(self.languages),
            processing_time=0,
        )
    
    def _process_easyocr(self, image: bytes) -> OCROutput:
        """Process with EasyOCR."""
        from io import BytesIO
        import numpy as np
        from PIL import Image
        
        img = Image.open(BytesIO(image))
        img_array = np.array(img)
        
        raw_results = self._reader.readtext(img_array)
        
        results = []
        texts = []
        
        for bbox, text, conf in raw_results:
            if text.strip():
                # Convert polygon bbox to rectangle
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                x, y = int(min(x_coords)), int(min(y_coords))
                w, h = int(max(x_coords) - x), int(max(y_coords) - y)
                
                results.append(OCRResult(
                    text=text,
                    confidence=conf,
                    bbox=(x, y, w, h),
                ))
                texts.append(text)
        
        return OCROutput(
            full_text=" ".join(texts),
            results=results,
            language="+".join(self.languages),
            processing_time=0,
        )
    
    def find_text(
        self,
        image: bytes,
        search_text: str,
        threshold: float = 0.7,
    ) -> Optional[OCRResult]:
        """
        Find specific text in an image.
        
        Args:
            image: Image bytes
            search_text: Text to search for
            threshold: Minimum confidence threshold
            
        Returns:
            OCRResult if found, None otherwise
        """
        output = self.process(image)
        search_lower = search_text.lower()
        
        for result in output.results:
            if (search_lower in result.text.lower() and 
                result.confidence >= threshold):
                return result
        
        return None
    
    def find_all_text(
        self,
        image: bytes,
        search_text: str,
        threshold: float = 0.7,
    ) -> List[OCRResult]:
        """
        Find all occurrences of text in an image.
        
        Args:
            image: Image bytes
            search_text: Text to search for
            threshold: Minimum confidence threshold
            
        Returns:
            List of matching OCRResults
        """
        output = self.process(image)
        search_lower = search_text.lower()
        
        return [
            result for result in output.results
            if search_lower in result.text.lower() and result.confidence >= threshold
        ]
    
    def get_ui_elements(
        self,
        image: bytes,
        element_types: List[str] = None,
    ) -> List[OCRResult]:
        """
        Detect UI elements (buttons, inputs, etc.) via text patterns.
        
        Args:
            image: Image bytes
            element_types: Types to detect (placeholder for future)
            
        Returns:
            List of detected UI element OCRResults
        """
        output = self.process(image)
        
        # Filter for likely UI elements (short text, high confidence)
        ui_elements = [
            result for result in output.results
            if len(result.text.split()) <= 3 and result.confidence > 0.8
        ]
        
        return ui_elements
