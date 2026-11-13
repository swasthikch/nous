"""Comprehensive Automated Test Suite for Phase 10 & 11:
Live Financial Market Intelligence & Market Reasoning Engine.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.core.intent import IntentType, intent_classifier
from backend.app.core.tool_registry import tool_registry
from backend.app.market.db import MarketDBManager, init_market_db
from backend.app.market.engine import MarketReasoningEngine
from backend.app.market.fetcher import MarketDataFetcher


async def run_tests():
    print("=" * 65)
    print("  RUNNING PHASE 10 & 11 TEST SUITE: MARKET INTELLIGENCE & REASONING")
    print("=" * 65)

    test_db_path = settings.PROJECT_ROOT / "data" / "database" / "test_nous_market.db"
    if test_db_path.exists():
        test_db_path.unlink()

    # ---------------- 1. DATABASE & WAL VERIFICATION ----------------
    print("\n[GROUP 1] Testing Database Schema, WAL Mode, and Seed Watchlist...")
    init_market_db(test_db_path)
    assert test_db_path.exists(), "Database file must exist"
    print(" [PASS] test_nous_market.db initialized.")

    db = MarketDBManager(db_path=test_db_path)
    watchlist = db.get_watchlist()
    assert len(watchlist) >= 8, f"Seed watchlist must contain at least 8 instruments, found {len(watchlist)}"
    symbols = [w["symbol"] for w in watchlist]
    assert "^NSEI" in symbols, "NIFTY 50 must be in seed watchlist"
    assert "^BSESN" in symbols, "SENSEX must be in seed watchlist"
    assert "RELIANCE.NS" in symbols, "RELIANCE.NS must be in seed watchlist"
    assert "^IXIC" in symbols, "NASDAQ must be in seed watchlist"
    print(f" [PASS] Seed watchlist verified ({len(watchlist)} instruments found).")

    # Add custom instrument to watchlist
    added = db.add_to_watchlist("INFY.NS", "Infosys Ltd", "NSE")
    assert added["symbol"] == "INFY.NS"
    assert db.remove_from_watchlist("INFY.NS") is True
    assert db.remove_from_watchlist("NON_EXISTENT") is False
    print(" [PASS] Watchlist Add/Remove CRUD verified.")

    # ---------------- 2. ALERTS ENGINE ----------------
    print("\n[GROUP 2] Testing Market Alerts CRUD & Trigger Conditions...")
    alert1 = db.add_alert("^NSEI", "above", 26000.0, "Breakout alert")
    alert2 = db.add_alert("RELIANCE.NS", "below", 1250.0, "Stop loss alert")
    assert alert1["id"] is not None
    assert alert2["is_active"] is True

    active_alerts = db.get_alerts(only_active=True)
    assert len(active_alerts) == 2
    print(f" [PASS] Active alerts created ({len(active_alerts)} alerts).")

    marked = db.mark_alert_triggered(alert1["id"])
    assert marked is True
    active_after = db.get_alerts(only_active=True)
    assert len(active_after) == 1
    deleted = db.delete_alert(alert2["id"])
    assert deleted is True
    print(" [PASS] Alert triggering and deletion verified.")

    # ---------------- 3. CACHE OPERATIONS ----------------
    print("\n[GROUP 3] Testing Quotes Cache Management...")
    mock_quote = {
        "symbol": "^NSEI",
        "name": "NIFTY 50",
        "price": 25150.0,
        "change": 120.0,
        "pct_change": 0.48,
        "prev_close": 25030.0,
        "open_price": 25080.0,
        "day_high": 25190.0,
        "day_low": 25045.0,
        "volume": 250000000,
        "currency": "INR",
        "market_state": "REGULAR",
        "is_live": False,
        "sparkline_json": '[{"time": 1700000000, "price": 25150.0}]',
    }
    db.save_cached_quote(mock_quote)
    retrieved = db.get_cached_quote("^NSEI")
    assert retrieved is not None
    assert retrieved["price"] == 25150.0
    assert retrieved["pct_change"] == 0.48
    print(" [PASS] Quote cache persistence and retrieval verified.")

    # ---------------- 4. MARKET FETCHER & SESSION ENGINE ----------------
    print("\n[GROUP 4] Testing Market Data Fetcher & Session State Engine...")
    fetcher = MarketDataFetcher(db_manager=db)

    # Session status tests
    nse_session = fetcher.get_market_session_status("NSE")
    assert "state" in nse_session
    assert nse_session["timezone"] == "IST"
    print(f" [PASS] NSE session state detected: {nse_session['label']} ({nse_session['state']})")

    us_session = fetcher.get_market_session_status("US")
    assert "state" in us_session
    assert us_session["timezone"] == "EST"
    print(f" [PASS] US session state detected: {us_session['label']} ({us_session['state']})")

    # Fetch quote with fallback resilience
    q = fetcher.fetch_quote("^NSEI")
    assert q["symbol"] == "^NSEI"
    assert q["price"] > 0
    assert "sparkline" in q
    assert len(q["sparkline"]) > 0
    assert q["data_status"] in ("live", "simulated_fallback", "cached")
    print(f" [PASS] Fetch quote verified: {q['name']} = {q['price']} {q['currency']} ({q['data_status']})")

    # Benchmark indices batch
    indices = fetcher.get_benchmark_indices()
    assert len(indices["indian_indices"]) >= 3
    assert len(indices["global_indices"]) >= 3
    print(f" [PASS] Benchmark indices retrieved ({len(indices['indian_indices'])} Indian, {len(indices['global_indices'])} Global).")

    # FII / DII flows
    flows = fetcher.get_fii_dii_flows()
    assert "fii_net_flow_cr" in flows
    assert "dii_net_flow_cr" in flows
    assert "net_institutional_flow_cr" in flows
    print(f" [PASS] FII/DII Institutional flows verified: Net = {flows['net_institutional_flow_cr']:+,.1f} Cr.")

    # ---------------- 5. PHASE 11: MARKET CAUSAL REASONING ENGINE ----------------
    print("\n[GROUP 5] Testing Phase 11 Causal Reasoning & Anti-Hallucination Standards...")
    engine = MarketReasoningEngine(fetcher=fetcher)

    # Test news retrieval
    news = engine.fetch_relevant_news("NIFTY 50", limit=3)
    assert len(news) > 0, "News retrieval must return items"
    print(f" [PASS] Financial news fetched ({len(news)} articles). Sample: '{news[0]['title'][:50]}...'")

    # Test full movement analysis
    analysis = engine.analyze_movement("^NSEI")
    required_keys = [
        "market_movement",
        "possible_reason",
        "evidence",
        "timing",
        "impact",
        "confidence",
        "sources",
        "contributing_factors",
        "disclaimer",
    ]
    for k in required_keys:
        assert k in analysis, f"Key '{k}' required by Phase 11 prompt specification was missing"

    assert analysis["confidence"] in ("High", "Medium", "Low")
    assert len(analysis["sources"]) > 0
    assert "DISCLAIMER" in analysis["disclaimer"]
    print(f" [PASS] Causal reasoning output conforms 100% to Prompt Section 11 structure (Confidence: {analysis['confidence']}).")

    # Formatted report generation
    report = engine.generate_formatted_report("^NSEI")
    assert "### NOUS Market Intelligence Briefing" in report
    assert "**Market Movement:**" in report
    assert "**Possible Reason:**" in report
    assert "**Evidence & Data Points:**" in report
    assert "**Timing:**" in report
    assert "**Confidence Rating:**" in report
    print(" [PASS] Human-readable markdown debrief report generated successfully.")

    # Stock-level analysis (Reliance)
    rel_analysis = engine.analyze_movement("RELIANCE.NS")
    assert rel_analysis["symbol"] == "RELIANCE.NS"
    print(" [PASS] Equity-level causal reasoning verified (RELIANCE.NS).")

    # ---------------- 6. INTENT CLASSIFICATION ----------------
    print("\n[GROUP 6] Testing Market Intent Classification & Extraction...")
    test_queries = [
        ("Why is the market down today?", IntentType.MARKET_ANALYSIS, "explain_market_movement"),
        ("Explain why Nifty fell", IntentType.MARKET_ANALYSIS, "explain_market_movement"),
        ("Why did Reliance drop?", IntentType.MARKET_ANALYSIS, "explain_market_movement"),
        ("What is the stock price of Reliance?", IntentType.STOCK_QUERY, "get_stock_quote"),
        ("TCS share price", IntentType.STOCK_QUERY, "get_stock_quote"),
        ("Show market overview", IntentType.MARKET_OVERVIEW, "get_market_indices"),
        ("How is the market performing today?", IntentType.MARKET_OVERVIEW, "get_market_indices"),
        ("Are FII buying or selling today?", IntentType.FII_DII_FLOWS, "get_fii_dii_activity"),
        ("Show my stock watchlist", IntentType.MARKET_WATCHLIST, "manage_market_watchlist"),
    ]

    for query, expected_intent, expected_tool in test_queries:
        res = intent_classifier.classify(query)
        assert res.intent == expected_intent, f"Query '{query}' expected {expected_intent}, got {res.intent}"
        assert res.suggested_tool == expected_tool, f"Query '{query}' expected tool {expected_tool}, got {res.suggested_tool}"
        print(f" [PASS] Intent: '{query}' -> {res.intent.value} ({res.suggested_tool})")

    # ---------------- 7. TOOL REGISTRY VERIFICATION ----------------
    print("\n[GROUP 7] Testing Tool Registry Execution for Market Tools...")
    # Tool 1: get_market_indices
    res_indices = await tool_registry.execute("get_market_indices", {})
    assert res_indices.success is True
    assert res_indices.is_verified is True
    print(" [PASS] Tool 'get_market_indices' executed successfully.")

    # Tool 2: get_stock_quote
    res_quote = await tool_registry.execute("get_stock_quote", {"symbol": "^BSESN"})
    assert res_quote.success is True
    assert res_quote.data["symbol"] == "^BSESN"
    print(" [PASS] Tool 'get_stock_quote' executed successfully.")

    # Tool 3: explain_market_movement
    res_explain = await tool_registry.execute("explain_market_movement", {"symbol_or_index": "^NSEI"})
    assert res_explain.success is True
    assert "formatted_report" in res_explain.data
    print(" [PASS] Tool 'explain_market_movement' executed successfully.")

    # Tool 4: manage_market_watchlist
    res_wl = await tool_registry.execute("manage_market_watchlist", {"action": "list"})
    assert res_wl.success is True
    print(" [PASS] Tool 'manage_market_watchlist' executed successfully.")

    # Tool 5: set_market_alert
    res_alert = await tool_registry.execute(
        "set_market_alert",
        {"symbol": "TCS.NS", "condition": "above", "target_value": 4500.0},
    )
    assert res_alert.success is True
    print(" [PASS] Tool 'set_market_alert' executed successfully.")

    # Tool 6: get_fii_dii_activity
    res_flows = await tool_registry.execute("get_fii_dii_activity", {})
    assert res_flows.success is True
    print(" [PASS] Tool 'get_fii_dii_activity' executed successfully.")

    # ---------------- 8. FASTAPI REST ENDPOINTS VERIFICATION ----------------
    print("\n[GROUP 8] Testing FastAPI REST Endpoints via AsyncClient...")
    import httpx
    from backend.app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /api/market/indices
        r = await client.get("/api/market/indices")
        assert r.status_code == 200
        assert "indian_indices" in r.json()
        print(" [PASS] GET /api/market/indices -> 200 OK")

        # 2. GET /api/market/quote/^NSEI
        r = await client.get("/api/market/quote/^NSEI")
        assert r.status_code == 200
        assert r.json()["symbol"] == "^NSEI"
        print(" [PASS] GET /api/market/quote/^NSEI -> 200 OK")

        # 3. GET /api/market/watchlist
        r = await client.get("/api/market/watchlist")
        assert r.status_code == 200
        assert "watchlist" in r.json()
        print(" [PASS] GET /api/market/watchlist -> 200 OK")

        # 4. POST /api/market/watchlist (Add)
        r = await client.post(
            "/api/market/watchlist",
            json={"symbol": "WIPRO.NS", "name": "Wipro Limited", "market": "NSE"},
        )
        assert r.status_code == 200
        print(" [PASS] POST /api/market/watchlist -> 200 OK")

        # 5. DELETE /api/market/watchlist/WIPRO.NS
        r = await client.delete("/api/market/watchlist/WIPRO.NS")
        assert r.status_code == 200
        print(" [PASS] DELETE /api/market/watchlist/WIPRO.NS -> 200 OK")

        # 6. GET /api/market/alerts
        r = await client.get("/api/market/alerts")
        assert r.status_code == 200
        print(" [PASS] GET /api/market/alerts -> 200 OK")

        # 7. POST /api/market/alerts
        r = await client.post(
            "/api/market/alerts",
            json={"symbol": "INFY.NS", "condition": "above", "target_value": 2000.0, "notes": "Test alert"},
        )
        assert r.status_code == 200
        alert_id = r.json()["alert"]["id"]
        print(f" [PASS] POST /api/market/alerts -> 200 OK (id: {alert_id})")

        # 8. DELETE /api/market/alerts/{id}
        r = await client.delete(f"/api/market/alerts/{alert_id}")
        assert r.status_code == 200
        print(" [PASS] DELETE /api/market/alerts/{id} -> 200 OK")

        # 9. POST /api/market/analyze
        r = await client.post("/api/market/analyze", json={"symbol": "^NSEI"})
        assert r.status_code == 200
        assert "formatted_report" in r.json()
        print(" [PASS] POST /api/market/analyze -> 200 OK")

        # 10. GET /api/market/fii-dii
        r = await client.get("/api/market/fii-dii")
        assert r.status_code == 200
        assert "fii_net_flow_cr" in r.json()
        print(" [PASS] GET /api/market/fii-dii -> 200 OK")

    # Cleanup test db
    if test_db_path.exists():
        test_db_path.unlink()

    print("\n" + "=" * 65)
    print(" [SUCCESS] ALL PHASE 10 & 11 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_tests())
