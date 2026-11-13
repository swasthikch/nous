"""Ollama Local Model Client for NOUS."""

import time
import httpx
from typing import Any, AsyncGenerator, Optional
from backend.app.config import settings


class OllamaClient:
    """Asynchronous client for interacting with the local Ollama instance."""

    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OLLAMA_MODEL
        # Use generous timeouts since local CPU inference can take a few seconds
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def check_connection(self) -> dict[str, Any]:
        """Check if Ollama is accessible and list installed models."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = self.default_model in models or any(
                        m.startswith(self.default_model) for m in models
                    )
                    return {
                        "status": "connected",
                        "available_models": models,
                        "configured_model": self.default_model,
                        "configured_model_available": model_found,
                    }
                return {
                    "status": "error",
                    "detail": f"Ollama returned HTTP status {response.status_code}",
                    "configured_model": self.default_model,
                }
        except httpx.ConnectError:
            return {
                "status": "disconnected",
                "detail": (
                    f"Could not connect to Ollama at {self.base_url}. "
                    "Ensure the Ollama application or background service is running."
                ),
                "configured_model": self.default_model,
            }
        except Exception as e:
            return {
                "status": "error",
                "detail": str(e),
                "configured_model": self.default_model,
            }

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send a non-streaming chat request to Ollama."""
        selected_model = model or self.default_model
        payload_messages = []

        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": selected_model,
            "messages": payload_messages,
            "stream": False,
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                elapsed = time.perf_counter() - start_time

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ollama error (HTTP {response.status_code}): {response.text}",
                        "model": selected_model,
                        "elapsed_seconds": round(elapsed, 2),
                    }

                result = response.json()
                message_content = result.get("message", {}).get("content", "")
                eval_count = result.get("eval_count", 0)
                eval_duration_ns = result.get("eval_duration", 1)
                tokens_per_second = (
                    round(eval_count / (eval_duration_ns / 1e9), 2)
                    if eval_duration_ns > 0 and eval_count > 0
                    else 0.0
                )

                return {
                    "success": True,
                    "model": selected_model,
                    "response": message_content,
                    "elapsed_seconds": round(elapsed, 2),
                    "eval_count": eval_count,
                    "tokens_per_second": tokens_per_second,
                }
        except httpx.ConnectError:
            return {
                "success": False,
                "error": f"Connection refused to Ollama at {self.base_url}. Make sure Ollama is running.",
                "model": selected_model,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception while communicating with Ollama: {str(e)}",
                "model": selected_model,
            }

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat tokens from Ollama."""
        selected_model = model or self.default_model
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": selected_model,
            "messages": payload_messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                if response.status_code != 200:
                    yield f"[Error: Ollama returned status {response.status_code}]"
                    return
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue


ollama_client = OllamaClient()
