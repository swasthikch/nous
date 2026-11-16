"""Safe Tool Registry and Sandboxed Executor for NOUS.

Provides:
- Schema validation for all tool inputs.
- 5-Tier permission gating (READ, PREPARE, WRITE, EXTERNAL_ACTION, SENSITIVE_ACTION).
- Cryptographic single-use approval tokens for high-impact actions.
- Asynchronous execution timeouts (preventing hung processes).
- Immutable security audit logging.
- Anti-hallucination verification guarantees.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

from backend.app.tools.permissions import (
    PermissionLevel,
    RiskLevel,
    risk_to_permission,
    permission_manager,
    PermissionCheckResult,
)
from backend.app.tools.approval import approval_manager, ApprovalRequest, ApprovalStatus
from backend.app.tools.logger import tool_logger


class ToolParameter(BaseModel):
    name: str
    type: str  # "string", "number", "integer", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter]
    permission_level: PermissionLevel = PermissionLevel.READ
    risk_level: Optional[RiskLevel] = RiskLevel.LOW
    timeout_seconds: float = 15.0


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    is_verified: bool = True
    requires_approval: bool = False
    approval_token: Optional[str] = None
    elapsed_seconds: float = 0.0


class SafeToolRegistry:
    """Master registry and sandboxed executor for all NOUS tools."""

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self.permission_mgr = permission_manager
        self.approval_mgr = approval_manager
        self.logger = tool_logger

    def register(
        self,
        name: str,
        description: str,
        parameters: list[ToolParameter],
        permission_level: PermissionLevel | RiskLevel | str = PermissionLevel.READ,
        risk_level: Optional[RiskLevel] = None,  # Backward compatibility
        timeout_seconds: float = 15.0,
    ) -> Callable:
        """Decorator to register a tool with permission classification and timeout bounds."""
        target_perm = risk_to_permission(risk_level) if risk_level is not None else risk_to_permission(permission_level)

        def decorator(func: Callable) -> Callable:
            defn = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                permission_level=target_perm,
                timeout_seconds=timeout_seconds,
            )
            self._tools[name] = {
                "definition": defn,
                "func": func,
                "permission_level": target_perm,
                "risk_level": target_perm,  # Backward compatibility
                "timeout_seconds": timeout_seconds,
            }
            return func

        return decorator

    def get_tool(self, name: str) -> Optional[dict[str, Any]]:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return [t["definition"] for t in self._tools.values()]

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions in standard JSON Schema format for LLMs."""
        definitions = []
        for name, tool in self._tools.items():
            defn: ToolDefinition = tool["definition"]
            definitions.append({
                "name": defn.name,
                "description": defn.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: {"type": p.type, "description": p.description}
                        for p in defn.parameters
                    },
                    "required": [p.name for p in defn.parameters if p.required],
                },
                "permission_level": defn.permission_level.value,
                "timeout_seconds": defn.timeout_seconds,
            })
        return definitions

    def _validate_parameters(
        self, defn: ToolDefinition, params: dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate input types and required fields against declared parameter schema."""
        for param in defn.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter '{param.name}' for tool '{defn.name}'."

            if param.name in params:
                val = params[param.name]
                if param.type == "number" and not isinstance(val, (int, float)):
                    return False, f"Parameter '{param.name}' must be a number, received {type(val).__name__}."
                elif param.type == "integer" and not isinstance(val, int):
                    return False, f"Parameter '{param.name}' must be an integer, received {type(val).__name__}."
                elif param.type == "boolean" and not isinstance(val, bool):
                    return False, f"Parameter '{param.name}' must be a boolean, received {type(val).__name__}."
                elif param.type == "string" and not isinstance(val, str):
                    return False, f"Parameter '{param.name}' must be a string, received {type(val).__name__}."
                elif param.type == "array" and not isinstance(val, list):
                    return False, f"Parameter '{param.name}' must be an array, received {type(val).__name__}."
                elif param.type == "object" and not isinstance(val, dict):
                    return False, f"Parameter '{param.name}' must be an object, received {type(val).__name__}."

        return True, None

    async def execute(
        self,
        tool_name: str,
        params: dict[str, Any],
        approval_token: Optional[str] = None,
        actor: str = "user",
    ) -> ToolResult:
        """Execute a tool through validation, permission gates, and timeout sandbox."""
        t0 = time.perf_counter()

        # 1. Existence Check
        tool = self._tools.get(tool_name)
        if not tool:
            elapsed = time.perf_counter() - t0
            self.logger.log(
                tool_name=tool_name,
                permission_level=PermissionLevel.READ,
                parameters=params,
                status="FAILED",
                elapsed_seconds=elapsed,
                actor=actor,
                error_message=f"Tool '{tool_name}' is not registered.",
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is not registered in NOUS.",
                is_verified=False,
                elapsed_seconds=round(elapsed, 3),
            )

        defn: ToolDefinition = tool["definition"]
        func: Callable = tool["func"]
        perm_level: PermissionLevel = defn.permission_level

        # 2. Schema Input Validation
        is_valid, val_err = self._validate_parameters(defn, params)
        if not is_valid:
            elapsed = time.perf_counter() - t0
            self.logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="FAILED",
                elapsed_seconds=elapsed,
                actor=actor,
                error_message=val_err,
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=val_err,
                is_verified=False,
                elapsed_seconds=round(elapsed, 3),
            )

        # 3. Permission Gate & Cryptographic Approval Verification
        check: PermissionCheckResult = self.permission_mgr.check_permission(tool_name, perm_level, params)

        if check.requires_approval:
            # Check if user provided an approved single-use token
            if approval_token:
                ok, req, reason = self.approval_mgr.approve_token(approval_token)
                if not ok:
                    elapsed = time.perf_counter() - t0
                    self.logger.log(
                        tool_name=tool_name,
                        permission_level=perm_level,
                        parameters=params,
                        status="BLOCKED",
                        elapsed_seconds=elapsed,
                        approval_token=approval_token,
                        actor=actor,
                        error_message=reason,
                    )
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=f"Authorization Blocked: {reason}",
                        is_verified=False,
                        requires_approval=True,
                        approval_token=approval_token,
                        elapsed_seconds=round(elapsed, 3),
                    )
            else:
                # Generate new approval token and wait for user confirmation
                req = self.approval_mgr.create_request(
                    tool_name=tool_name,
                    parameters=params,
                    permission_level=perm_level,
                    description=f"Action '{tool_name}' is classified as {perm_level.value.upper()} and requires confirmation.",
                )
                elapsed = time.perf_counter() - t0
                self.logger.log(
                    tool_name=tool_name,
                    permission_level=perm_level,
                    parameters=params,
                    status="BLOCKED",
                    elapsed_seconds=elapsed,
                    approval_token=req.token,
                    actor=actor,
                    error_message=f"Action paused. Awaiting user confirmation token '{req.token[:8]}...'",
                )
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"User authorization required for {perm_level.value.upper()} action '{tool_name}'. Approval token issued.",
                    is_verified=False,
                    requires_approval=True,
                    approval_token=req.token,
                    elapsed_seconds=round(elapsed, 3),
                )

        # 4. Asynchronous Execution Sandbox with Timeouts
        try:
            if inspect.iscoroutinefunction(func):
                result_data = await asyncio.wait_for(
                    func(**params),
                    timeout=defn.timeout_seconds,
                )
            else:
                # Run synchronous blocking tools in default executor
                loop = asyncio.get_running_loop()
                result_data = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: func(**params)),
                    timeout=defn.timeout_seconds,
                )

            elapsed = time.perf_counter() - t0
            self.logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="SUCCESS",
                elapsed_seconds=elapsed,
                approval_token=approval_token,
                actor=actor,
            )

            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result_data,
                is_verified=True,
                requires_approval=False,
                approval_token=approval_token,
                elapsed_seconds=round(elapsed, 3),
            )

        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - t0
            err_msg = f"Tool '{tool_name}' exceeded execution timeout limit of {defn.timeout_seconds} seconds."
            self.logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="TIMEOUT",
                elapsed_seconds=elapsed,
                approval_token=approval_token,
                actor=actor,
                error_message=err_msg,
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=err_msg,
                is_verified=False,
                elapsed_seconds=round(elapsed, 3),
            )

        except Exception as e:
            elapsed = time.perf_counter() - t0
            err_msg = f"Execution error in tool '{tool_name}': {str(e)}"
            self.logger.log(
                tool_name=tool_name,
                permission_level=perm_level,
                parameters=params,
                status="FAILED",
                elapsed_seconds=elapsed,
                approval_token=approval_token,
                actor=actor,
                error_message=err_msg,
            )
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=err_msg,
                is_verified=False,
                elapsed_seconds=round(elapsed, 3),
            )


# Global Safe Registry Singleton
safe_tool_registry = SafeToolRegistry()
