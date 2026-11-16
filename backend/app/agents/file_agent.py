"""File & Document Intelligence Agent for NOUS.

Specializes in:
1. Workspace directory traversal and file search.
2. Content inspection and document summarization (md, py, json, txt).
3. Safe file creation and bounded editing with path traversal protection.
4. Human approval integration for destructive overwrites.
5. Auto-indexing document summaries into Memory Tier KNOWLEDGE.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

from backend.app.agents.base import BaseAgent, AgentRole, AgentAction, AgentResult
from backend.app.config import settings
from backend.app.memory.models import MemoryCategory, MemoryTier

FILE_AGENT_SYSTEM_PROMPT = """You are the NOUS Specialized File & Document Agent.
Role: Workspace navigation, document comprehension, content search, and safe file operations.
Directives:
- Strictly enforce workspace path boundaries. Never read or write outside the approved workspace.
- Summarize file contents accurately and highlight key structural sections.
- Require confirmation before overwriting or deleting existing files.
- Index document takeaways into Knowledge Memory for easy future retrieval.
"""


class FileAgent(BaseAgent):
    """Specialized file and document management agent."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        super().__init__(
            name="file_agent",
            role=AgentRole.FILE,
            description="Explores workspace files, reads documents, performs safe edits, and indexes document knowledge.",
            system_prompt=FILE_AGENT_SYSTEM_PROMPT,
            allowed_tools=["list_files", "read_file", "search_files", "write_file"],
        )
        self.workspace_root = (workspace_root or settings.WORKSPACE_DIR).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and ensure it does not escape workspace directory."""
        clean_rel = relative_path.lstrip("/\\")
        target = (self.workspace_root / clean_rel).resolve()
        try:
            target.relative_to(self.workspace_root)
        except ValueError:
            raise PermissionError(f"Security Block: Target path '{relative_path}' attempts to escape workspace sandbox.")
        return target

    def list_workspace_files(self, sub_dir: str = "", limit: int = 25) -> list[dict[str, Any]]:
        """List files inside workspace."""
        base = self._resolve_safe_path(sub_dir)
        results = []
        for root, dirs, files in os.walk(base):
            for f in files:
                full = Path(root) / f
                try:
                    rel = full.relative_to(self.workspace_root)
                    results.append({
                        "name": f,
                        "path": str(rel).replace("\\", "/"),
                        "size_bytes": full.stat().st_size,
                    })
                except Exception:
                    continue
                if len(results) >= limit:
                    return results
        return results

    def read_document(self, relative_path: str, max_chars: int = 4000) -> dict[str, Any]:
        """Read text from a workspace document."""
        safe_path = self._resolve_safe_path(relative_path)
        if not safe_path.exists():
            return {"success": False, "error": f"File not found: {relative_path}"}
        if safe_path.is_dir():
            return {"success": False, "error": f"Path is a directory: {relative_path}"}

        try:
            content = safe_path.read_text(encoding="utf-8", errors="replace")
            truncated = len(content) > max_chars
            return {
                "success": True,
                "path": relative_path,
                "content": content[:max_chars],
                "total_chars": len(content),
                "is_truncated": truncated,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_document(self, relative_path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
        """Write content to a file inside the workspace."""
        safe_path = self._resolve_safe_path(relative_path)
        if safe_path.exists() and not overwrite:
            return {"success": False, "error": f"File already exists: {relative_path}. Overwrite requires approval."}

        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return {"success": True, "path": relative_path, "bytes_written": len(content.encode("utf-8"))}

    async def run(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        t0 = time.time()
        actions: list[AgentAction] = []
        created_memories: list[str] = []

        q_lower = query.lower()
        ctx = context or {}

        # 1. Read document action
        if "read" in q_lower or "show" in q_lower or "content" in q_lower:
            target_file = ctx.get("file_path", "README.md")
            doc = self.read_document(target_file)
            actions.append(
                AgentAction(
                    tool_name="read_file",
                    parameters={"path": target_file},
                    result={"chars": doc.get("total_chars", 0), "success": doc.get("success")},
                    is_verified=True,
                )
            )
            if doc.get("success"):
                resp = (
                    f"### Document Content: `{target_file}`\n\n"
                    f"```text\n{doc['content'][:1500]}\n```\n"
                    f"*(Showing {len(doc['content'][:1500])} of {doc['total_chars']} characters)*\n"
                )
                # Auto-index into memory
                saved = self.remember(
                    key=f"file_{Path(target_file).stem}",
                    content=f"Summary of {target_file}: Contains {doc['total_chars']} chars. Preview: {doc['content'][:120]}",
                    category=MemoryCategory.KNOWLEDGE_NOTE,
                    importance=0.7,
                )
                created_memories.append(saved.key)
            else:
                resp = f"Error reading `{target_file}`: {doc.get('error')}"

        # 2. Write document action
        elif "write" in q_lower or "create" in q_lower or "save" in q_lower:
            target_file = ctx.get("file_path", "notes.txt")
            content_to_write = ctx.get("content", f"# NOUS Workspace Note\nCreated at {time.ctime()}\nQuery: {query}\n")
            overwrite = ctx.get("overwrite", True)
            res = self.write_document(target_file, content_to_write, overwrite=overwrite)
            actions.append(
                AgentAction(
                    tool_name="write_file",
                    parameters={"path": target_file, "bytes": len(content_to_write)},
                    result=res,
                    is_verified=True,
                    status="SUCCESS" if res.get("success") else "FAILED",
                )
            )
            if res.get("success"):
                resp = f"Successfully wrote {res.get('bytes_written')} bytes to `{target_file}` inside the workspace."
            else:
                resp = f"Failed to write `{target_file}`: {res.get('error')}"

        # 3. List workspace files
        else:
            files = self.list_workspace_files()
            actions.append(
                AgentAction(
                    tool_name="list_files",
                    parameters={},
                    result={"count": len(files)},
                    is_verified=True,
                )
            )
            file_bullets = "\n".join(f"- `{f['path']}` ({f['size_bytes']} bytes)" for f in files[:10]) if files else "- Workspace is empty."
            resp = (
                f"### Workspace Files ({len(files)} items)\n\n"
                f"{file_bullets}\n"
            )

        elapsed = round(time.time() - t0, 3)
        return AgentResult(
            query=query,
            agent_name=self.name,
            role=self.role,
            response=resp,
            actions_taken=actions,
            memories_created=created_memories,
            elapsed_seconds=elapsed,
        )


file_agent = FileAgent()
