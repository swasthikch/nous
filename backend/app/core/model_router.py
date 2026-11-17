"""Intelligent Model Router for Hybrid AI Architecture.

Selects between local (Ollama) and cloud models based on user preference,
task complexity, local model availability, and network status.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.core.ollama_client import ollama_client
from backend.app.core.cloud_provider import cloud_provider
from backend.app.core.intent import IntentResult, IntentType


class RoutingMode(str, Enum):
    LOCAL = "local"     # Force local processing (Ollama)
    CLOUD = "cloud"     # Force cloud processing (if configured)
    HYBRID = "hybrid"   # Intelligent auto-routing based on task complexity


class RoutingDecision(BaseModel):
    selected_target: str       # "local" or "cloud"
    selected_model: str        # e.g. "qwen2.5:3b" or "gpt-4o-mini"
    mode: RoutingMode
    reason: str
    fallback_available: bool


class ModelRouter:
    """Intelligently routes inference requests between local and cloud backends."""

    def __init__(self, default_mode: RoutingMode = RoutingMode.HYBRID):
        self.mode = default_mode

    def set_mode(self, mode: RoutingMode):
        """Update operational mode (local, cloud, or hybrid)."""
        self.mode = mode

    async def route(
        self,
        intent: IntentResult,
        requested_model: Optional[str] = None,
    ) -> RoutingDecision:
        """Determine whether to use local or cloud model."""
        # 0. Offline Lockdown Policy Check (Phase 14)
        try:
            from backend.app.security.vault import security_vault
            if security_vault.is_offline_lockdown_enabled():
                return RoutingDecision(
                    selected_target="local",
                    selected_model=settings.OLLAMA_MODEL,
                    mode=RoutingMode.LOCAL,
                    reason="Security Policy Enforcement: Offline Lockdown is active. External cloud inference is blocked.",
                    fallback_available=False,
                )
        except Exception:
            pass

        # 1. Explicit model override
        if requested_model:
            if requested_model.startswith("cloud:") or requested_model == cloud_provider.model:
                clean_model = requested_model.replace("cloud:", "")
                return RoutingDecision(
                    selected_target="cloud",
                    selected_model=clean_model,
                    mode=self.mode,
                    reason=f"User explicitly requested cloud model: {clean_model}",
                    fallback_available=True,
                )
            else:
                return RoutingDecision(
                    selected_target="local",
                    selected_model=requested_model,
                    mode=self.mode,
                    reason=f"User explicitly requested local model: {requested_model}",
                    fallback_available=cloud_provider.is_configured(),
                )

        # 2. Mode: LOCAL
        if self.mode == RoutingMode.LOCAL:
            return RoutingDecision(
                selected_target="local",
                selected_model=settings.OLLAMA_MODEL,
                mode=self.mode,
                reason="System set to Local-Only mode. Prioritizing local privacy and zero API cost.",
                fallback_available=False,
            )

        # 3. Mode: CLOUD
        if self.mode == RoutingMode.CLOUD:
            if cloud_provider.is_configured():
                return RoutingDecision(
                    selected_target="cloud",
                    selected_model=cloud_provider.model,
                    mode=self.mode,
                    reason="System set to Cloud-Only mode.",
                    fallback_available=True,
                )
            else:
                return RoutingDecision(
                    selected_target="local",
                    selected_model=settings.OLLAMA_MODEL,
                    mode=self.mode,
                    reason="Cloud requested but cloud API key is not configured. Falling back to local Ollama.",
                    fallback_available=False,
                )

        # 4. Mode: HYBRID (Intelligent Routing)
        if intent.requires_cloud_routing and cloud_provider.is_configured():
            return RoutingDecision(
                selected_target="cloud",
                selected_model=cloud_provider.model,
                mode=self.mode,
                reason="Task requires complex reasoning/analysis. Routed to cloud model for superior capability.",
                fallback_available=True,
            )

        # In hybrid mode: check if local Ollama is available; if not available but cloud is configured, seamlessly route to cloud!
        if cloud_provider.is_configured():
            try:
                from backend.app.core.ollama_client import ollama_client
                conn = await ollama_client.check_connection()
                if conn.get("status") != "connected":
                    return RoutingDecision(
                        selected_target="cloud",
                        selected_model=cloud_provider.model,
                        mode=self.mode,
                        reason="Local Ollama is offline. Hybrid router seamlessly directed request to configured Cloud model.",
                        fallback_available=False,
                    )
            except Exception:
                pass

        # Standard hybrid fallback: use local for routine chats, calculations, and privacy
        return RoutingDecision(
            selected_target="local",
            selected_model=settings.OLLAMA_MODEL,
            mode=self.mode,
            reason="Standard conversational query or local tool operation. Routed to local quantized model.",
            fallback_available=cloud_provider.is_configured(),
        )


model_router = ModelRouter()
