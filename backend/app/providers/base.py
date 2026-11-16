"""Abstract Base Provider Interface for NOUS Model Engines.

Defines the contract that any LLM provider (local Ollama, OpenAI, Groq,
OpenRouter, Anthropic, Gemini) must implement. This ensures NOUS can switch
between models seamlessly without rewriting application logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional
from pydantic import BaseModel, Field


class StreamChunk(BaseModel):
    """A single token or delta chunk emitted during streaming inference."""
    content: str = ""
    is_final: bool = False
    finish_reason: Optional[str] = None
    tokens_per_second: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    """The complete result of non-streaming inference."""
    content: str
    model: str
    elapsed_seconds: float
    tokens_per_second: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class ProviderHealth(BaseModel):
    """Status report for a model provider."""
    provider_name: str
    status: str  # "connected", "disconnected", "unconfigured", "error"
    configured_model: str
    available_models: list[str] = Field(default_factory=list)
    model_ready: bool = False
    detail: Optional[str] = None


class BaseModelProvider(ABC):
    """Abstract Base Class for LLM inference providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the unique name of this provider (e.g. 'ollama', 'cloud_openai')."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Check endpoint connectivity and list installed/available models."""
        pass

    @abstractmethod
    async def get_available_models(self) -> list[str]:
        """Return a list of model identifiers available on this provider."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> ProviderResponse:
        """Execute non-streaming inference and return the complete response."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response tokens chunk-by-chunk for real-time output."""
        pass
