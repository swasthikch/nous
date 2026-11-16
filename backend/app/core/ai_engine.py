"""Central AI Orchestration Brain for NOUS (Phase 1 Refactored).

Maintains complete backward-compatibility with all existing test suites
and subsystems by delegating to the unified CentralOrchestrator.
"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Optional

from backend.app.core.model_router import RoutingDecision
from backend.app.ai_core.orchestrator import (
    CentralOrchestrator,
    OrchestratorResponse,
    ToolExecutionRecord,
    orchestrator,
)

# Backward-compatible type aliases
AIEngineResponse = OrchestratorResponse
AIEngine = CentralOrchestrator

# Global singleton pointing to the central orchestrator
ai_brain = orchestrator
