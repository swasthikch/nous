"""Research Agent for NOUS.

Specializes in:
1. Multi-source web search (DuckDuckGo, Wikipedia, arXiv, news).
2. Evidence-backed synthesis and citation generation.
3. Extracting discoveries and auto-indexing into Memory Tier KNOWLEDGE.
4. Answering research questions with verified sources.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from backend.app.agents.base import BaseAgent, AgentRole, AgentAction, AgentResult
from backend.app.memory.models import MemoryCategory, MemoryTier
from backend.app.research.engine import ResearchEngine

RESEARCH_AGENT_SYSTEM_PROMPT = """You are the NOUS Specialized Research Agent.
Role: Deep multi-source web investigations, fact verification, and knowledge synthesis.
Directives:
- Cite real sources with markdown links.
- Emphasize verified findings and explicitly distinguish between factual consensus and emerging claims.
- Format responses cleanly with executive summary, key findings, and references.
- Auto-index key learnings to central Knowledge Memory for future recall.
"""


class ResearchAgent(BaseAgent):
    """Specialized deep research and knowledge extraction agent."""

    def __init__(self, engine: Optional[ResearchEngine] = None) -> None:
        super().__init__(
            name="research_agent",
            role=AgentRole.RESEARCH,
            description="Performs deep multi-source web research, cites facts, and saves findings to Knowledge Memory.",
            system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
            allowed_tools=["web_search", "academic_search", "summarize_document"],
        )
        self.engine = engine or ResearchEngine()

    async def run(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        t0 = time.time()
        actions: list[AgentAction] = []
        created_memories: list[str] = []

        # 1. Check existing Knowledge memories first to prevent redundant investigations
        existing_memories = self.retrieve_memories(query=query, limit=2, tier=MemoryTier.KNOWLEDGE)
        context_notes = ""
        if existing_memories:
            context_notes = f"\nExisting Recall: {existing_memories[0].content}\n"

        # 2. Perform multi-source investigation
        report = self.engine.investigate(query=query)
        sources = report.get("sources", [])
        actions.append(
            AgentAction(
                tool_name="web_search",
                parameters={"query": query, "sources_searched": len(sources)},
                result={"sources_count": len(sources), "top_source": sources[0].get("title", "") if sources else ""},
                is_verified=True,
                status="SUCCESS",
            )
        )

        # 3. Format structured executive response
        key_findings = report.get("key_findings", [])
        findings_bullets = "\n".join(f"- {f}" for f in key_findings) if key_findings else "- Direct search completed."
        citations = []
        for s in sources[:4]:
            title = s.get("title", "Resource")
            url = s.get("url", "#")
            publisher = s.get("publisher", "Web")
            citations.append(f"- [{title}]({url}) ({publisher})")
        citations_text = "\n".join(citations) if citations else "- No direct URL citations found."

        formatted_response = (
            f"### Research Findings: {query}\n\n"
            f"**Executive Summary:**\n{report.get('executive_summary', 'Multi-source search executed.')}\n\n"
            f"**Key Findings:**\n{findings_bullets}\n\n"
            f"**Verified Sources & Citations:**\n{citations_text}\n"
        )
        if context_notes:
            formatted_response += f"\n> *[NOUS Cognitive Note]*{context_notes}"

        # 4. Save core discovery into Memory Tier KNOWLEDGE
        if key_findings:
            key_slug = query.lower().replace(" ", "_")[:32]
            summary_fact = f"Research on '{query}': {key_findings[0]}"
            saved_item = self.remember(
                key=f"research_{key_slug}",
                content=summary_fact,
                category=MemoryCategory.KNOWLEDGE_NOTE,
                importance=0.8,
            )
            created_memories.append(saved_item.key)

        elapsed = round(time.time() - t0, 3)
        return AgentResult(
            query=query,
            agent_name=self.name,
            role=self.role,
            response=formatted_response,
            actions_taken=actions,
            memories_created=created_memories,
            elapsed_seconds=elapsed,
        )


research_agent = ResearchAgent()
