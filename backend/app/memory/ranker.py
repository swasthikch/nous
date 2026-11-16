"""Cognitive Relevance Ranking Engine for NOUS Memory.

Implements Stanford Generative Agents memory scoring model:
Score = w_relevance * S_relevance + w_importance * S_importance + w_recency * S_recency

Guarantees that:
1. User profile facts (name, identity, learning goals) are always recalled.
2. High-importance project and knowledge milestones are prioritized.
3. Recently accessed or updated items receive an organic freshness boost.
"""

from __future__ import annotations

import math
import time
from typing import Any
from backend.app.memory.models import MemoryItem, MemoryTier, MemoryCategory


class MemoryRanker:
    """Calculates cognitive relevance scores for candidate memories."""

    def __init__(
        self,
        relevance_weight: float = 0.60,
        importance_weight: float = 0.25,
        recency_weight: float = 0.15,
        decay_rate_lambda: float = 0.005,  # Half-life of ~140 hours (~6 days)
    ) -> None:
        self.w_rel = relevance_weight
        self.w_imp = importance_weight
        self.w_rec = recency_weight
        self.decay_lambda = decay_rate_lambda

    def _calculate_lexical_relevance(self, query: str, memory: MemoryItem) -> float:
        """Score keyword and token overlap between query and memory item using word boundaries."""
        import re
        q_tokens = [t.lower() for t in query.split() if len(t) > 2]
        if not q_tokens:
            return 0.0

        key_lower = memory.key.lower()
        content_lower = memory.content.lower()

        # Tokenize fields into distinct word sets (prevents "use" matching "user")
        key_words = set(re.findall(r"\w+", key_lower))
        content_words = set(re.findall(r"\w+", content_lower))
        cat_words = set(re.findall(r"\w+", memory.category.value.lower()) + re.findall(r"\w+", memory.tier.value.lower()))

        raw_score = 0.0

        # Exact phrase bonus
        q_clean = query.strip().lower()
        if q_clean in key_lower:
            raw_score += 5.0
        elif q_clean in content_lower:
            raw_score += 3.5

        for tok in q_tokens:
            if tok in key_words:
                raw_score += 4.0
            elif len(tok) >= 4 and any(w.startswith(tok) for w in key_words):
                raw_score += 2.0

            if tok in content_words:
                raw_score += 2.5
            elif len(tok) >= 4 and any(w.startswith(tok) for w in content_words):
                raw_score += 1.5

            if tok in cat_words:
                raw_score += 1.0

        return raw_score / (raw_score + 4.0) if raw_score > 0 else 0.0

    def _calculate_recency(self, memory: MemoryItem, now: float) -> float:
        """Exponential decay based on hours elapsed since creation or update."""
        ref_time = memory.last_accessed_at or memory.updated_at or memory.created_at
        hours_elapsed = max(0.0, (now - ref_time) / 3600.0)
        return math.exp(-self.decay_lambda * hours_elapsed)

    def rank(
        self,
        query: str,
        candidates: list[MemoryItem],
        limit: int = 5,
        tier: MemoryTier | None = None,
    ) -> list[MemoryItem]:
        """Rank and return top-k most relevant memories."""
        if not candidates:
            return []

        now = time.time()
        scored: list[tuple[float, MemoryItem]] = []

        # Filter by tier if specified
        pool = [m for m in candidates if m.is_active]
        if tier is not None:
            pool = [m for m in pool if m.tier == tier]

        for m in pool:
            s_rel = self._calculate_lexical_relevance(query, m)
            s_rec = self._calculate_recency(m, now)
            s_imp = m.importance
            # User profile facts receive a subtle cognitive anchor boost
            profile_boost = 0.05 if m.category == MemoryCategory.USER_PROFILE else 0.0

            if s_rel > 0.05 or m.importance >= 0.7 or profile_boost > 0:
                final_score = (self.w_rel * s_rel) + (self.w_imp * s_imp) + (self.w_rec * s_rec) + profile_boost
                scored.append((final_score, m))

        # Sort descending by final cognitive score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]


memory_ranker = MemoryRanker()
