"""Ollama Local Model Provider for NOUS.

Provides high-performance local inference with zero cloud cost and full privacy.
Supports both non-streaming and real-time token-by-token streaming via Ollama's
native HTTP API.
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Optional
import httpx

from backend.app.config import settings
from backend.app.providers.base import (
    BaseModelProvider,
    ProviderHealth,
    ProviderResponse,
    StreamChunk,
)


class OllamaProvider(BaseModelProvider):
    """Local inference provider communicating with an Ollama daemon."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OLLAMA_MODEL
        self.timeout = httpx.Timeout(timeout_seconds, connect=5.0)

    def get_provider_name(self) -> str:
        return "ollama"

    async def check_health(self) -> ProviderHealth:
        """Query Ollama /api/tags to confirm daemon is active and list models."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    is_ready = self.default_model in models or any(
                        m.startswith(self.default_model) for m in models
                    )
                    return ProviderHealth(
                        provider_name=self.get_provider_name(),
                        status="connected",
                        configured_model=self.default_model,
                        available_models=models,
                        model_ready=is_ready,
                        detail="Ollama daemon is connected and healthy.",
                    )
                return ProviderHealth(
                    provider_name=self.get_provider_name(),
                    status="error",
                    configured_model=self.default_model,
                    detail=f"Ollama returned HTTP status {res.status_code}: {res.text[:120]}",
                )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return ProviderHealth(
                provider_name=self.get_provider_name(),
                status="disconnected",
                configured_model=self.default_model,
                detail=(
                    f"Could not connect to Ollama at {self.base_url}. "
                    "Ensure the Ollama application or background service is running on your machine."
                ),
            )
        except Exception as e:
            return ProviderHealth(
                provider_name=self.get_provider_name(),
                status="error",
                configured_model=self.default_model,
                detail=str(e),
            )

    async def get_available_models(self) -> list[str]:
        health = await self.check_health()
        return health.available_models

    def _prepare_payload(
        self,
        messages: list[dict[str, str]],
        model: Optional[str],
        temperature: float,
        stream: bool,
        system_prompt: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        target_model = model or self.default_model
        payload_messages: list[dict[str, str]] = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": target_model,
            "messages": payload_messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            },
        }
        return target_model, payload

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> ProviderResponse:
        """Execute non-streaming inference."""
        target_model, payload = self._prepare_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            stream=False,
            system_prompt=system_prompt,
        )

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                elapsed = time.perf_counter() - t0

                if res.status_code == 200:
                    data = res.json()
                    msg = data.get("message", {})
                    content = msg.get("content", "")

                    eval_count = data.get("eval_count", 0)
                    eval_duration = data.get("eval_duration", 0)
                    tps = 0.0
                    if eval_duration > 0 and eval_count > 0:
                        tps = round(eval_count / (eval_duration / 1e9), 2)

                    return ProviderResponse(
                        content=content,
                        model=target_model,
                        elapsed_seconds=round(elapsed, 2),
                        tokens_per_second=tps,
                        prompt_tokens=data.get("prompt_eval_count", 0),
                        completion_tokens=eval_count,
                        metadata=data,
                        success=True,
                    )

                return ProviderResponse(
                    content="",
                    model=target_model,
                    elapsed_seconds=round(elapsed, 2),
                    success=False,
                    error=f"Ollama HTTP {res.status_code}: {res.text[:200]}",
                )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            elapsed = time.perf_counter() - t0
            return ProviderResponse(
                content="",
                model=target_model,
                elapsed_seconds=round(elapsed, 2),
                success=False,
                error=f"Could not connect to Ollama at {self.base_url}. Ensure Ollama is running.",
            )
        except Exception as e:
            elapsed = time.perf_counter() - t0
            return ProviderResponse(
                content="",
                model=target_model,
                elapsed_seconds=round(elapsed, 2),
                success=False,
                error=str(e),
            )

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream tokens chunk-by-chunk from Ollama."""
        target_model, payload = self._prepare_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            stream=True,
            system_prompt=system_prompt,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as stream_res:
                    if stream_res.status_code != 200:
                        err_text = await stream_res.aread()
                        yield StreamChunk(
                            content=f"Error from Ollama (HTTP {stream_res.status_code}): {err_text.decode('utf-8', errors='ignore')[:200]}",
                            is_final=True,
                            finish_reason="error",
                        )
                        return

                    async for line in stream_res.aiter_lines():
                        if not line or not line.strip():
                            continue
                        try:
                            chunk_data = json.loads(line)
                            msg = chunk_data.get("message", {})
                            delta = msg.get("content", "")
                            is_done = chunk_data.get("done", False)

                            tps = None
                            if is_done:
                                eval_count = chunk_data.get("eval_count", 0)
                                eval_dur = chunk_data.get("eval_duration", 0)
                                if eval_dur > 0 and eval_count > 0:
                                    tps = round(eval_count / (eval_dur / 1e9), 2)

                            yield StreamChunk(
                                content=delta,
                                is_final=is_done,
                                finish_reason="stop" if is_done else None,
                                tokens_per_second=tps,
                                metadata=chunk_data if is_done else {},
                            )
                        except json.JSONDecodeError:
                            continue
        except (httpx.ConnectError, httpx.ConnectTimeout):
            yield StreamChunk(
                content=f"Error: Could not connect to Ollama at {self.base_url}. Ensure the Ollama service is running.",
                is_final=True,
                finish_reason="connection_error",
            )
        except Exception as e:
            yield StreamChunk(
                content=f"Streaming error: {str(e)}",
                is_final=True,
                finish_reason="error",
            )
