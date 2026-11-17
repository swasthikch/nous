"""Cloud Model Provider for NOUS.

Provides official OpenAI-compatible API integration for cloud inference
(OpenAI, Groq, OpenRouter, DeepSeek, Mistral, Google Gemini via OpenAI-compat).
Supports both non-streaming and real-time Server-Sent Events (SSE) token streaming.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, AsyncGenerator, Optional
import httpx

from backend.app.providers.base import (
    BaseModelProvider,
    ProviderHealth,
    ProviderResponse,
    StreamChunk,
)


class CloudModelProvider(BaseModelProvider):
    """Cloud model provider for any OpenAI-compatible completions endpoint."""

    def __init__(self) -> None:
        self.api_key: str = (
            os.getenv("CLOUD_API_KEY", "")
            or os.getenv("GROQ_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
            or os.getenv("GEMINI_API_KEY", "")
        ).strip()

        raw_enabled = os.getenv("CLOUD_PROVIDER_ENABLED")
        if raw_enabled is not None:
            self.enabled: bool = raw_enabled.lower() in ("true", "1", "yes")
        else:
            self.enabled = bool(self.api_key)

        raw_provider = os.getenv("CLOUD_PROVIDER_NAME", "").strip().lower()
        raw_url = os.getenv("CLOUD_BASE_URL", "").strip()
        raw_model = os.getenv("CLOUD_MODEL", "").strip()

        if self.api_key.startswith("gsk_"):
            self.provider_name: str = raw_provider or "groq"
            self.base_url: str = (raw_url or "https://api.groq.com/openai/v1").rstrip("/")
            self.default_model: str = raw_model or "qwen/qwen3.8-27b"
        elif self.api_key.startswith("AIza"):
            self.provider_name = raw_provider or "gemini"
            self.base_url: str = (raw_url or "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
            self.default_model = raw_model or "gemini-1.5-flash"
        else:
            self.provider_name = raw_provider or "openai"
            self.base_url = (raw_url or "https://api.openai.com/v1").rstrip("/")
            self.default_model = raw_model or "gpt-4o-mini"

        self.timeout = httpx.Timeout(60.0, connect=10.0)

    def get_provider_name(self) -> str:
        return f"cloud_{self.provider_name}"

    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key.strip())

    async def check_health(self) -> ProviderHealth:
        """Check if cloud provider is configured and can authenticate."""
        if not self.is_configured():
            return ProviderHealth(
                provider_name=self.get_provider_name(),
                status="unconfigured",
                configured_model=self.default_model,
                available_models=[],
                model_ready=False,
                detail="Cloud provider is disabled or CLOUD_API_KEY is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/models", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                    if models and self.default_model not in models:
                        if "llama-3.1-8b-instant" in models:
                            self.default_model = "llama-3.1-8b-instant"
                        else:
                            self.default_model = models[0]
                    return ProviderHealth(
                        provider_name=self.get_provider_name(),
                        status="connected",
                        configured_model=self.default_model,
                        available_models=models,
                        model_ready=self.default_model in models or bool(models),
                        detail="Cloud API endpoint connected and authenticated.",
                    )
                return ProviderHealth(
                    provider_name=self.get_provider_name(),
                    status="error",
                    configured_model=self.default_model,
                    detail=f"Cloud provider returned HTTP {res.status_code}: {res.text[:200]}",
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
        max_tokens: Optional[int] = None,
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        target_model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload_messages: list[dict[str, str]] = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        return target_model, headers, payload

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> ProviderResponse:
        """Execute non-streaming inference via cloud API."""
        if not self.is_configured():
            return ProviderResponse(
                content="",
                model=model or self.default_model,
                elapsed_seconds=0.0,
                success=False,
                error="Cloud provider is not configured. Please set CLOUD_API_KEY.",
            )

        target_model, headers, payload = self._prepare_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            stream=False,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 404 and self.provider_name == "groq":
                    for alt in ("qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
                        if alt != target_model:
                            payload["model"] = alt
                            retry_res = await client.post(
                                f"{self.base_url}/chat/completions",
                                headers=headers,
                                json=payload,
                            )
                            if retry_res.status_code == 200:
                                res = retry_res
                                target_model = alt
                                self.default_model = alt
                                break

                elapsed = time.perf_counter() - t0

                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    content = choices[0].get("message", {}).get("content", "") if choices else ""
                    usage = data.get("usage", {})
                    comp_tokens = usage.get("completion_tokens", 0)
                    tps = round(comp_tokens / elapsed, 2) if elapsed > 0 and comp_tokens > 0 else 0.0

                    return ProviderResponse(
                        content=content,
                        model=target_model,
                        elapsed_seconds=round(elapsed, 2),
                        tokens_per_second=tps,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=comp_tokens,
                        metadata=data,
                        success=True,
                    )

                return ProviderResponse(
                    content="",
                    model=target_model,
                    elapsed_seconds=round(elapsed, 2),
                    success=False,
                    error=f"Cloud API HTTP {res.status_code}: {res.text[:200]}",
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
        """Stream response tokens chunk-by-chunk from cloud API."""
        if not self.is_configured():
            yield StreamChunk(
                content="Error: Cloud provider is not configured. Please set CLOUD_API_KEY.",
                is_final=True,
                finish_reason="unconfigured",
            )
            return

        target_model, headers, payload = self._prepare_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            stream=True,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as stream_res:
                    if stream_res.status_code != 200:
                        err_text = await stream_res.aread()
                        if stream_res.status_code == 404 and self.provider_name == "groq":
                            for alt in ("qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"):
                                if alt == target_model:
                                    continue
                                payload["model"] = alt
                                self.default_model = alt
                                try:
                                    async with client.stream(
                                        "POST",
                                        f"{self.base_url}/chat/completions",
                                        headers=headers,
                                        json=payload,
                                    ) as retry_res:
                                        if retry_res.status_code == 200:
                                            async for line in retry_res.aiter_lines():
                                                if not line or not line.strip():
                                                    continue
                                                if line.startswith("data: "):
                                                    raw_data = line[6:].strip()
                                                    if raw_data == "[DONE]":
                                                        yield StreamChunk(content="", is_final=True, finish_reason="stop")
                                                        break
                                                    try:
                                                        chunk_data = json.loads(raw_data)
                                                        choices = chunk_data.get("choices", [])
                                                        if choices:
                                                            delta = choices[0].get("delta", {}).get("content", "")
                                                            finish_reason = choices[0].get("finish_reason")
                                                            is_done = bool(finish_reason)
                                                            yield StreamChunk(
                                                                content=delta,
                                                                is_final=is_done,
                                                                finish_reason=finish_reason,
                                                            )
                                                    except json.JSONDecodeError:
                                                        pass
                                            return
                                except Exception:
                                    continue

                        yield StreamChunk(
                            content=f"Error from cloud provider (HTTP {stream_res.status_code}): {err_text.decode('utf-8', errors='ignore')[:200]}",
                            is_final=True,
                            finish_reason="error",
                        )
                        return

                    async for line in stream_res.aiter_lines():
                        if not line or not line.strip():
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                yield StreamChunk(content="", is_final=True, finish_reason="stop")
                                break
                            try:
                                chunk_data = json.loads(raw_data)
                                choices = chunk_data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {}).get("content", "")
                                    finish_reason = choices[0].get("finish_reason")
                                    is_done = bool(finish_reason)
                                    yield StreamChunk(
                                        content=delta,
                                        is_final=is_done,
                                        finish_reason=finish_reason,
                                    )
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            yield StreamChunk(
                content=f"Cloud streaming error: {str(e)}",
                is_final=True,
                finish_reason="error",
            )
