"""Conversational Memory Extractor for NOUS.

Passively extracts high-value personal facts, learning goals, project decisions,
and preferences from natural conversation without saving every message as memory.
Enforces zero-trust redaction: passwords, API keys, and credentials are never stored.
"""

from __future__ import annotations

import re
from typing import Any, Optional
from pydantic import BaseModel

from backend.app.memory.models import MemoryCategory, MemoryTier, category_to_tier
from backend.app.security.redactor import sensitive_redactor


class ExtractedCandidate(BaseModel):
    tier: MemoryTier
    category: MemoryCategory
    key: str
    content: str
    importance: float
    confidence: float


class ConversationalMemoryExtractor:
    """Extracts long-term candidate memories from user messages."""

    def __init__(self) -> None:
        # Regex patterns for deterministic, zero-latency fact extraction
        self.profile_patterns = [
            (
                re.compile(r"\b(?:my name is|call me|i am|i'm)\s+([A-Z][a-zA-Z0-9_\-]{2,25})\b", re.I),
                "preferred_name",
                MemoryCategory.USER_PROFILE,
                0.95,
            ),
            (
                re.compile(r"\bi (?:am a|work as an?)\s+([a-zA-Z\s]{3,35})\b", re.I),
                "user_role",
                MemoryCategory.USER_PROFILE,
                0.85,
            ),
            (
                re.compile(r"\bi (?:am learning|am studying|want to learn|am interested in)\s+([a-zA-Z0-9\s#\+\-\.]{3,45})\b", re.I),
                "learning_goal",
                MemoryCategory.USER_PROFILE,
                0.80,
            ),
        ]

        self.preference_patterns = [
            (
                re.compile(r"\bi (?:prefer|always use|favor)\s+([a-zA-Z0-9\s\.\-_#\+]{2,30})\s+(?:over|instead of)\s+([a-zA-Z0-9\s\.\-_#\+]{2,30})\b", re.I),
                "preference",
                MemoryCategory.PERSONAL_INFO,
                0.85,
            ),
            (
                re.compile(r"\bi (?:like|love|dislike|hate)\s+([a-zA-Z0-9\s\.\-_#\+]{3,40})\b", re.I),
                "preference_general",
                MemoryCategory.PERSONAL_INFO,
                0.70,
            ),
        ]

        self.project_patterns = [
            (
                re.compile(r"\bwe are (?:using|building with|implementing)\s+([a-zA-Z0-9\s\.\-_#\+]{3,40})\s+for\s+([a-zA-Z0-9\s\.\-_#\+]{3,40})\b", re.I),
                "project_architecture",
                MemoryCategory.PROJECT,
                0.85,
            ),
            (
                re.compile(r"\b(?:the project deadline|my deadline|due date) is\s+([a-zA-Z0-9\s,]{3,30})\b", re.I),
                "project_deadline",
                MemoryCategory.PROJECT,
                0.90,
            ),
        ]

        self.explicit_remember_pattern = re.compile(
            r"^(?:nous,?\s*)?(?:remember that|save this:?|don't forget that|take note that)\s+(.+)$",
            re.IGNORECASE,
        )

    def extract_candidates(self, user_message: str) -> list[ExtractedCandidate]:
        """Scan a user message and return extracted candidate memories."""
        text = user_message.strip()
        if not text or len(text) < 5 or text.endswith("?"):
            return []

        # 1. Zero-Trust Security Gate: Never extract credentials or secrets
        if sensitive_redactor.contains_sensitive(text):
            return []

        candidates: list[ExtractedCandidate] = []

        # 2. Check Explicit "Remember That..." Commands
        exp_match = self.explicit_remember_pattern.match(text)
        if exp_match:
            raw_fact = exp_match.group(1).strip()
            # Generate key from first few words
            words = [w.lower() for w in re.findall(r"\w+", raw_fact) if len(w) > 2]
            key = "_".join(words[:4]) or "user_note"
            candidates.append(
                ExtractedCandidate(
                    tier=MemoryTier.PERSONAL,
                    category=MemoryCategory.PERSONAL_INFO,
                    key=key,
                    content=raw_fact,
                    importance=0.85,
                    confidence=0.95,
                )
            )
            return candidates

        # 3. Check User Profile Statements
        for pattern, key_prefix, cat, conf in self.profile_patterns:
            m = pattern.search(text)
            if m:
                val = m.group(1).strip()
                candidates.append(
                    ExtractedCandidate(
                        tier=category_to_tier(cat),
                        category=cat,
                        key=key_prefix,
                        content=f"User stated: {m.group(0).strip()}",
                        importance=0.90,
                        confidence=conf,
                    )
                )

        # 4. Check Preferences
        for pattern, key_prefix, cat, conf in self.preference_patterns:
            m = pattern.search(text)
            if m:
                candidates.append(
                    ExtractedCandidate(
                        tier=category_to_tier(cat),
                        category=cat,
                        key=f"{key_prefix}_{len(candidates)}",
                        content=m.group(0).strip(),
                        importance=0.70,
                        confidence=conf,
                    )
                )

        # 5. Check Project Technical Decisions
        for pattern, key_prefix, cat, conf in self.project_patterns:
            m = pattern.search(text)
            if m:
                candidates.append(
                    ExtractedCandidate(
                        tier=category_to_tier(cat),
                        category=cat,
                        key=f"{key_prefix}_{len(candidates)}",
                        content=m.group(0).strip(),
                        importance=0.85,
                        confidence=conf,
                    )
                )

        return candidates


memory_extractor = ConversationalMemoryExtractor()
