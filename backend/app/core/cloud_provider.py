"""Configurable Cloud Model Provider Interface for NOUS.

Supports official OpenAI-compatible endpoints (OpenAI, Groq, OpenRouter, DeepSeek,
Mistral, Gemini via OpenAI endpoint).
API keys are loaded securely from environment variables—never hardcoded.
"""

import os
import time
import httpx
from typing import Any, AsyncGenerator, Optional
from dotenv import load_dotenv

load_dotenv()


class CloudProvider:
    """Configurable client for official cloud AI model APIs."""

    def __init__(self):
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
            self.model: str = raw_model or "llama-3.3-70b-versatile"
        elif self.api_key.startswith("AIza"):
            self.provider_name = raw_provider or "gemini"
            self.base_url = (raw_url or "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
            self.model: str = raw_model or "gemini-1.5-flash"
        else:
            self.provider_name = raw_provider or "openai"
            self.base_url = (raw_url or "https://api.openai.com/v1").rstrip("/")
            self.model: str = raw_model or "gpt-4o-mini"

        self.default_model: str = self.model
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    def is_configured(self) -> bool:
        """Check if cloud provider is enabled and has an API key configured."""
        return self.enabled and bool(self.api_key.strip())

    async def check_health(self) -> dict[str, Any]:
        """Test cloud endpoint connectivity."""
        if not self.is_configured():
            return {
                "status": "unconfigured",
                "detail": "Cloud provider is disabled or CLOUD_API_KEY is not configured.",
                "provider": self.provider_name,
                "model": self.model,
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/models", headers=headers)
                if res.status_code == 200:
                    return {
                        "status": "connected",
                        "provider": self.provider_name,
                        "model": self.model,
                    }
                return {
                    "status": "error",
                    "detail": f"Cloud provider returned HTTP {res.status_code}: {res.text[:200]}",
                    "provider": self.provider_name,
                }
        except Exception as e:
            return {
                "status": "error",
                "detail": f"Failed to connect to cloud provider: {str(e)}",
                "provider": self.provider_name,
            }

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send chat request to cloud provider."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Cloud provider is not configured. Please set CLOUD_API_KEY.",
                "model": self.model,
            }

        selected_model = model or self.model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                elapsed = time.perf_counter() - start_time

                if res.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Cloud API error (HTTP {res.status_code}): {res.text}",
                        "model": selected_model,
                        "elapsed_seconds": round(elapsed, 2),
                    }

                data = res.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "model": selected_model,
                    "provider": self.provider_name,
                    "elapsed_seconds": round(elapsed, 2),
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Cloud connection exception: {str(e)}",
                "model": selected_model,
            }


cloud_provider = CloudProvider()
