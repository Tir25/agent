"""
LLM Engine - Ollama/Llama Integration

This module provides the interface to the local LLM running via Ollama.
Supports text and vision (multimodal) inputs with Llama 3.2 Vision.
"""

import base64
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, Union

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    model: str
    tokens_used: int
    done: bool


class LLMEngine:
    """
    Local LLM Engine using Ollama.
    
    Provides text and vision inference capabilities using Llama 3.2 Vision.
    All processing happens locally - no data leaves your machine.
    """
    
    def __init__(
        self,
        model: str = "llama3.2-vision",
        host: str = "http://localhost:11434",
        temperature: float = 0.7,
        context_length: int = 8192,
    ):
        """
        Initialize the LLM Engine.
        
        Args:
            model: Ollama model name (default: llama3.2-vision)
            host: Ollama API host URL
            temperature: Sampling temperature (0.0 - 1.0)
            context_length: Maximum context window size
        """
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.context_length = context_length
        self._client = httpx.Client(timeout=120.0)
        
        logger.info(f"LLM Engine initialized with model: {model}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[list[Union[str, Path, bytes]]] = None,
        stream: bool = False,
    ) -> Union[LLMResponse, Generator[str, None, None]]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt/query
            system_prompt: Optional system prompt for context
            images: Optional list of images (paths, base64 strings, or bytes)
            stream: Whether to stream the response
            
        Returns:
            LLMResponse or generator of response chunks if streaming
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_length,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if images:
            payload["images"] = self._process_images(images)
        
        if stream:
            return self._stream_generate(payload)
        else:
            return self._sync_generate(payload)
    
    def _sync_generate(self, payload: dict) -> LLMResponse:
        """Synchronous generation."""
        try:
            response = self._client.post(
                f"{self.host}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("response", ""),
                model=data.get("model", self.model),
                tokens_used=data.get("eval_count", 0),
                done=data.get("done", True),
            )
        except httpx.HTTPError as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def _stream_generate(self, payload: dict) -> Generator[str, None, None]:
        """Streaming generation."""
        try:
            with self._client.stream(
                "POST",
                f"{self.host}/api/generate",
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if chunk := data.get("response"):
                            yield chunk
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            logger.error(f"LLM streaming failed: {e}")
            raise
    
    def _process_images(self, images: list) -> list[str]:
        """Convert images to base64 strings."""
        processed = []
        for img in images:
            if isinstance(img, bytes):
                processed.append(base64.b64encode(img).decode("utf-8"))
            elif isinstance(img, (str, Path)):
                path = Path(img)
                if path.exists():
                    with open(path, "rb") as f:
                        processed.append(base64.b64encode(f.read()).decode("utf-8"))
                else:
                    # Assume it's already base64
                    processed.append(str(img))
        return processed
    
    def chat(
        self,
        messages: list[dict],
        images: Optional[list] = None,
        stream: bool = False,
    ) -> Union[LLMResponse, Generator[str, None, None]]:
        """
        Chat-style interaction with conversation history.
        
        Args:
            messages: List of {"role": "user|assistant|system", "content": "..."}
            images: Optional images for the last message
            stream: Whether to stream the response
            
        Returns:
            LLMResponse or generator of response chunks
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_length,
            }
        }
        
        if images:
            # Add images to the last user message
            payload["messages"][-1]["images"] = self._process_images(images)
        
        if stream:
            return self._stream_chat(payload)
        else:
            return self._sync_chat(payload)
    
    def _sync_chat(self, payload: dict) -> LLMResponse:
        """Synchronous chat."""
        try:
            response = self._client.post(
                f"{self.host}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self.model),
                tokens_used=data.get("eval_count", 0),
                done=data.get("done", True),
            )
        except httpx.HTTPError as e:
            logger.error(f"LLM chat failed: {e}")
            raise
    
    def _stream_chat(self, payload: dict) -> Generator[str, None, None]:
        """Streaming chat."""
        try:
            with self._client.stream(
                "POST",
                f"{self.host}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if chunk := data.get("message", {}).get("content"):
                            yield chunk
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            logger.error(f"LLM chat streaming failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = self._client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(self.model) for m in models)
        except httpx.HTTPError:
            return False
    
    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()
