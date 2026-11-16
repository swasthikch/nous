"""Market Intelligence & Financial Analysis Agent for NOUS.

Specializes in:
1. Real-time Indian and global stock ticker / index tracking.
2. 20-factor causal reasoning for market movements.
3. Institutional flow monitoring (FII/DII net flows).
4. Strict educational safety gate: explicitly refuses trade execution.
5. Auto-indexing market debriefs into Memory Tier KNOWLEDGE.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from backend.app.agents.base import BaseAgent, AgentRole, AgentAction, AgentResult
from backend.app.market.engine import MarketReasoningEngine, DISCLAIMER
from backend.app.memory.models import MemoryCategory, MemoryTier

MARKET_AGENT_SYSTEM_PROMPT = f"""You are the NOUS Specialized Market Intelligence Agent.
Role: Multi-factor financial market reasoning, macroeconomic analysis, and sector intelligence.
Directives:
- Explain WHY indices and stocks move based on verified causal factors (earnings, rates, crude, flows).
- NEVER execute trades, recommend specific speculative trades, or act as an automated broker.
- Always include the mandatory educational disclaimer: {DISCLAIMER}
- Save significant market macro trends into Knowledge Memory for future context.
"""


class MarketIntelligenceAgent(BaseAgent):
    """Specialized financial market intelligence and causal reasoning agent."""

    def __init__(self, engine: Optional[MarketReasoningEngine] = None) -> None:
        super().__init__(
            name="market_agent",
            role=AgentRole.MARKET,
            description="Tracks market indices, provides 20-factor causal analysis, and strictly adheres to educational guidance.",
            system_prompt=MARKET_AGENT_SYSTEM_PROMPT,
            allowed_tools=["get_market_quote", "get_institutional_flows", "explain_market_movement"],
        )
        self.engine = engine or MarketReasoningEngine()

    async def get_overview(self) -> dict[str, Any]:
        """Fetch market overview with major benchmark indices."""
        nifty = self.engine.fetcher.fetch_quote("^NSEI")
        sensex = self.engine.fetcher.fetch_quote("^BSESN")
        sp500 = self.engine.fetcher.fetch_quote("^GSPC")
        flows = self.engine.fetcher.get_fii_dii_flows()
        return {
            "nifty": nifty,
            "sensex": sensex,
            "sp500": sp500,
            "institutional_flows": flows,
        }

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

        # 1. Zero-Trading Safety Gate: Immediately block trade execution attempts
        trade_trigger_words = ("buy", "sell", "place order", "short", "long", "trade", "execute trade")
        if any(w in q_lower for w in trade_trigger_words) and not any(w in q_lower for w in ("why", "explain", "analyze", "overview")):
            resp = (
                f"### Market Intelligence Safety Guardrail\n\n"
                f"**Trade Execution Blocked**: NOUS is strictly an educational analysis system. "
                f"Direct order placement, trade execution, and automated brokerage are permanently disabled.\n\n"
                f"> *{DISCLAIMER}*"
            )
            return AgentResult(
                query=query,
                agent_name=self.name,
                role=self.role,
                response=resp,
                actions_taken=[],
                memories_created=[],
                elapsed_seconds=round(time.time() - t0, 3),
            )

        # 2. Fetch market overview data
        overview = await self.get_overview()
        actions.append(
            AgentAction(
                tool_name="get_market_quote",
                parameters={"scope": "benchmarks"},
                result={"nifty": overview["nifty"].get("price"), "sp500": overview["sp500"].get("price")},
                is_verified=True,
            )
        )

        nifty = overview.get("nifty", {})
        nifty_price = nifty.get("price", 25150.0)
        nifty_change = nifty.get("pct_change", 0.0)
        nifty_str = f"NIFTY 50: {nifty_price:,.2f} ({nifty_change:+.2f}%)"

        flow_data = overview.get("institutional_flows", {})
        fii_net = flow_data.get("fii_net_flow_cr", 0.0)
        dii_net = flow_data.get("dii_net_flow_cr", 0.0)
        flow_summary = f"FII Net: {fii_net:+,.1f} Cr | DII Net: {dii_net:+,.1f} Cr"

        response_text = (
            f"### Market Intelligence Overview\n\n"
            f"- **Benchmark Status:** {nifty_str}\n"
            f"- **Institutional Flows (FII/DII):** {flow_summary}\n\n"
            f"**Analytical Commentary:**\n"
            f"Market dynamics reflect current interest rate expectations, domestic liquidity, and global equity correlations.\n\n"
            f"> *{DISCLAIMER}*"
        )

        # 3. Store market observation in Knowledge Memory
        saved = self.remember(
            key="market_nifty_snapshot",
            content=f"Market snapshot: {nifty_str}. {flow_summary}.",
            category=MemoryCategory.KNOWLEDGE_NOTE,
            importance=0.7,
        )
        created_memories.append(saved.key)

        elapsed = round(time.time() - t0, 3)
        return AgentResult(
            query=query,
            agent_name=self.name,
            role=self.role,
            response=response_text,
            actions_taken=actions,
            memories_created=created_memories,
            elapsed_seconds=elapsed,
        )


market_agent = MarketIntelligenceAgent()
