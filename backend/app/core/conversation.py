"""Conversation Context and Session Manager for NOUS.

Handles multi-turn memory buffers, context pruning within token budgets,
and file-backed session persistence across application restarts.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from backend.app.config import PROJECT_ROOT


class Message(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text")
    timestamp: float = Field(default_factory=time.time)
    metadata: Optional[dict] = Field(default_factory=dict)


class Session(BaseModel):
    id: str
    title: str
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    messages: list[Message] = Field(default_factory=list)


class ConversationManager:
    """Manages active chat sessions, context budgeting, and disk persistence."""

    def __init__(self, storage_dir: Optional[Path] = None, max_context_tokens: int = 3500):
        self.storage_dir = storage_dir or (PROJECT_ROOT / "data" / "sessions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_context_tokens = max_context_tokens
        self.active_sessions: dict[str, Session] = {}
        self._load_all_sessions()

    def _estimate_tokens(self, text: str) -> int:
        """Heuristic token estimation (~4 chars/token in English/code)."""
        return max(1, len(text) // 4)

    def _get_session_path(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}.json"

    def _load_all_sessions(self):
        """Load saved sessions from data/sessions/."""
        for file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                session = Session(**data)
                self.active_sessions[session.id] = session
            except Exception as e:
                print(f"[CONVERSATION] Could not load session {file.name}: {e}")

    def save_session(self, session: Session):
        """Persist session state to disk."""
        session.updated_at = time.time()
        file_path = self._get_session_path(session.id)
        try:
            file_path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[CONVERSATION ERROR] Failed to save session {session.id}: {e}")

    def create_session(self, title: str = "New Conversation") -> Session:
        """Create and store a new conversation session."""
        session_id = str(uuid.uuid4())[:8]
        session = Session(id=session_id, title=title)
        self.active_sessions[session_id] = session
        self.save_session(session)
        return session

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Retrieve existing session or spawn a fresh one."""
        if session_id and session_id in self.active_sessions:
            return self.active_sessions[session_id]
        return self.create_session()

    def list_sessions(self) -> list[dict]:
        """List all available sessions ordered by most recent activity."""
        sessions = list(self.active_sessions.values())
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages),
            }
            for s in sessions
        ]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> Message:
        """Append message to session and persist."""
        session = self.get_or_create_session(session_id)
        msg = Message(role=role, content=content, metadata=metadata or {})
        session.messages.append(msg)

        # Automatically update title if it's the first user message
        if role == "user" and len([m for m in session.messages if m.role == "user"]) == 1:
            clean_title = content.strip().split("\n")[0][:36]
            session.title = clean_title or "Conversation"

        self.save_session(session)
        return msg

    def get_context_window(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """Assemble an optimized context window fitting within the token budget.
        
        Guarantees:
        1. System prompt is always preserved at index 0.
        2. Most recent turns are preserved first.
        3. Exceeding token limit trims oldest turns safely.
        """
        session = self.get_or_create_session(session_id)
        context: list[dict[str, str]] = []

        total_tokens = 0
        if system_prompt:
            total_tokens += self._estimate_tokens(system_prompt)

        # Process messages in reverse (newest to oldest)
        recent_messages: list[dict[str, str]] = []
        for msg in reversed(session.messages):
            msg_tokens = self._estimate_tokens(msg.content)
            if total_tokens + msg_tokens > self.max_context_tokens:
                break  # Context budget reached
            recent_messages.append({"role": msg.role, "content": msg.content})
            total_tokens += msg_tokens

        # Restore chronological order
        recent_messages.reverse()

        if system_prompt:
            context.append({"role": "system", "content": system_prompt})
        context.extend(recent_messages)

        return context

    def delete_session(self, session_id: str) -> bool:
        """Delete session from memory and disk."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            file_path = self._get_session_path(session_id)
            if file_path.exists():
                file_path.unlink()
            return True
        return False

    def clear_session(self, session_id: str) -> bool:
        """Clear all messages in a session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].messages = []
            self.save_session(self.active_sessions[session_id])
            return True
        return False


conversation_manager = ConversationManager()
