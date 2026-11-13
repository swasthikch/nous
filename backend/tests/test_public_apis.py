from __future__ import annotations

"""Comprehensive Automated Test Suite for Public APIs Integration.

Tests curated keyless public APIs from https://github.com/public-apis/public-apis:
1. Open-Meteo Weather API
2. Free Dictionary API
3. Frankfurter Currency Exchange API
4. Official Joke API

Covers Service Client, Tool Registry execution, Intent Classification,
FastAPI REST endpoints, and Anti-Hallucination AIEngine guarantees.
"""

import asyncio
from pathlib import Path
import sys
import time

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure stdout is line buffered
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

import httpx

from backend.app.services.public_apis import (
    public_api_service,
    PublicAPIService,
    FALLBACK_DICTIONARY,
    FALLBACK_EXCHANGE_RATES_EUR,
)
from backend.app.core.tool_registry import tool_registry
from backend.app.core.intent import intent_classifier, IntentType
from backend.app.core.ai_engine import AIEngine
from backend.app.main import app as main_app


async def run_public_apis_tests() -> None:
    print("=" * 70, flush=True)
    print("  RUNNING PUBLIC APIS TEST SUITE (public-apis/public-apis)", flush=True)
    print("=" * 70, flush=True)

    # ---------------- 1. SERVICE CLIENT: WEATHER API ----------------
    print("\n[GROUP 1] Testing Weather Service (Open-Meteo / wttr.in)...", flush=True)
    weather_res = await public_api_service.get_weather("London")
    assert weather_res["success"] is True
    assert "temperature_c" in weather_res
    assert "condition" in weather_res
    assert weather_res["is_verified"] is True
    print(f" [PASS] Weather for London: {weather_res['temperature_c']}°C, {weather_res['condition']} (Source: {weather_res['source']})", flush=True)

    # Test empty location handling
    empty_weather = await public_api_service.get_weather("")
    assert empty_weather["success"] is False
    print(" [PASS] Empty location handled safely with success=False.", flush=True)

    # ---------------- 2. SERVICE CLIENT: DICTIONARY API ----------------
    print("\n[GROUP 2] Testing Lexical Service (Free Dictionary API)...", flush=True)
    dict_res = await public_api_service.lookup_definition("algorithm")
    assert dict_res["success"] is True
    assert dict_res["word"] == "algorithm"
    assert "primary_definition" in dict_res
    assert len(dict_res["meanings"]) > 0
    assert dict_res["is_verified"] is True
    print(f" [PASS] Definition of 'algorithm': {dict_res['primary_definition'][:65]}...", flush=True)

    # Test offline curated term
    nous_res = await public_api_service.lookup_definition("nous")
    assert nous_res["success"] is True
    assert nous_res["word"] == "nous"
    assert "intellect" in nous_res["primary_definition"].lower() or "mind" in nous_res["primary_definition"].lower()
    print(f" [PASS] Curated offline lookup for 'nous': {nous_res['primary_definition']}", flush=True)

    # Test empty word handling
    empty_dict = await public_api_service.lookup_definition("")
    assert empty_dict["success"] is False
    print(" [PASS] Empty word handled safely with success=False.", flush=True)

    # ---------------- 3. SERVICE CLIENT: CURRENCY EXCHANGE ----------------
    print("\n[GROUP 3] Testing Currency Conversion (Frankfurter API / ECB)...", flush=True)
    curr_res = await public_api_service.convert_currency(100.0, "USD", "EUR")
    assert curr_res["success"] is True
    assert curr_res["from_currency"] == "USD"
    assert curr_res["to_currency"] == "EUR"
    assert curr_res["converted_amount"] > 0
    assert curr_res["exchange_rate"] > 0
    assert curr_res["is_verified"] is True
    print(f" [PASS] 100 USD = {curr_res['converted_amount']} EUR (Rate: {curr_res['exchange_rate']}, Source: {curr_res['source']})", flush=True)

    # Identity conversion
    id_res = await public_api_service.convert_currency(250.0, "USD", "USD")
    assert id_res["success"] is True
    assert id_res["converted_amount"] == 250.0
    assert id_res["exchange_rate"] == 1.0
    print(" [PASS] Identity currency conversion (USD -> USD) evaluated instantly at 1.0 rate.", flush=True)

    # Negative / zero amount error
    invalid_curr = await public_api_service.convert_currency(-50.0, "USD", "EUR")
    assert invalid_curr["success"] is False
    print(" [PASS] Negative currency amount rejected safely.", flush=True)

    # ---------------- 4. SERVICE CLIENT: HUMOR & JOKES ----------------
    print("\n[GROUP 4] Testing Humor Service (Official Joke API)...", flush=True)
    joke_prog = await public_api_service.get_random_joke("programming")
    assert joke_prog["success"] is True
    assert len(joke_prog["setup"]) > 0
    assert len(joke_prog["punchline"]) > 0
    assert joke_prog["is_verified"] is True
    print(f" [PASS] Programming Joke: Q: {joke_prog['setup']} | A: {joke_prog['punchline']}", flush=True)

    joke_gen = await public_api_service.get_random_joke("general")
    assert joke_gen["success"] is True
    assert len(joke_gen["setup"]) > 0
    print(f" [PASS] General Joke: Q: {joke_gen['setup']} | A: {joke_gen['punchline']}", flush=True)

    # ---------------- 5. TOOL REGISTRY VERIFICATION ----------------
    print("\n[GROUP 5] Testing Tool Registry Execution & Anti-Hallucination...", flush=True)
    weather_tool = await tool_registry.execute("get_weather_forecast", {"location": "Tokyo"})
    assert weather_tool.success is True
    assert weather_tool.is_verified is True
    assert "temperature_c" in weather_tool.data
    print(" [PASS] Tool 'get_weather_forecast' executed and verified.", flush=True)

    dict_tool = await tool_registry.execute("lookup_dictionary_definition", {"word": "heuristic"})
    assert dict_tool.success is True
    assert dict_tool.is_verified is True
    assert "primary_definition" in dict_tool.data
    print(" [PASS] Tool 'lookup_dictionary_definition' executed and verified.", flush=True)

    curr_tool = await tool_registry.execute("convert_currency", {"amount": 75.0, "from_currency": "EUR", "to_currency": "GBP"})
    assert curr_tool.success is True
    assert curr_tool.is_verified is True
    assert curr_tool.data["converted_amount"] > 0
    print(" [PASS] Tool 'convert_currency' executed and verified.", flush=True)

    joke_tool = await tool_registry.execute("get_random_joke", {"category": "programming"})
    assert joke_tool.success is True
    assert joke_tool.is_verified is True
    print(" [PASS] Tool 'get_random_joke' executed and verified.", flush=True)

    # ---------------- 6. INTENT CLASSIFIER ROUTING ----------------
    print("\n[GROUP 6] Testing Heuristic Intent Classification...", flush=True)

    i_weather = intent_classifier.classify("What is the weather in Paris today?")
    assert i_weather.intent == IntentType.WEATHER_QUERY
    assert i_weather.suggested_tool == "get_weather_forecast"
    assert i_weather.tool_parameters.get("location") == "Paris"
    print(f" [PASS] Weather query correctly mapped: location='{i_weather.tool_parameters.get('location')}'.", flush=True)

    i_dict = intent_classifier.classify("What does algorithm mean?")
    assert i_dict.intent == IntentType.DICTIONARY_LOOKUP
    assert i_dict.suggested_tool == "lookup_dictionary_definition"
    assert i_dict.tool_parameters.get("word") == "algorithm"
    print(f" [PASS] Dictionary query correctly mapped: word='{i_dict.tool_parameters.get('word')}'.", flush=True)

    i_curr = intent_classifier.classify("convert 150 USD to EUR")
    assert i_curr.intent == IntentType.CURRENCY_CONVERT
    assert i_curr.suggested_tool == "convert_currency"
    assert i_curr.tool_parameters.get("amount") == 150.0
    assert i_curr.tool_parameters.get("from_currency") == "USD"
    assert i_curr.tool_parameters.get("to_currency") == "EUR"
    print(" [PASS] Currency conversion correctly mapped: 150.0 USD -> EUR.", flush=True)

    i_joke = intent_classifier.classify("tell me a programming joke")
    assert i_joke.intent == IntentType.RANDOM_JOKE
    assert i_joke.suggested_tool == "get_random_joke"
    assert i_joke.tool_parameters.get("category") == "programming"
    print(" [PASS] Joke query correctly mapped: category='programming'.", flush=True)

    # ---------------- 7. FASTAPI HTTP REST ENDPOINTS ----------------
    print("\n[GROUP 7] Testing FastAPI Public API HTTP Endpoints...", flush=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main_app), base_url="http://testserver") as client:
        # Weather
        r_w = await client.get("/api/public/weather", params={"location": "Berlin"})
        assert r_w.status_code == 200
        w_json = r_w.json()
        assert w_json["success"] is True
        print(f" [PASS] GET /api/public/weather -> {w_json['location']}: {w_json['temperature_c']}°C", flush=True)

        # Dictionary
        r_d = await client.get("/api/public/dictionary", params={"word": "intelligence"})
        assert r_d.status_code == 200
        d_json = r_d.json()
        assert d_json["success"] is True
        print(f" [PASS] GET /api/public/dictionary -> '{d_json['word']}': {d_json['primary_definition'][:50]}...", flush=True)

        # Currency
        r_c = await client.get("/api/public/currency", params={"amount": 50, "from_currency": "GBP", "to_currency": "USD"})
        assert r_c.status_code == 200
        c_json = r_c.json()
        assert c_json["success"] is True
        print(f" [PASS] GET /api/public/currency -> 50 GBP = {c_json['converted_amount']} USD", flush=True)

        # Joke
        r_j = await client.get("/api/public/joke", params={"category": "general"})
        assert r_j.status_code == 200
        j_json = r_j.json()
        assert j_json["success"] is True
        print(f" [PASS] GET /api/public/joke -> {j_json['setup']}", flush=True)

    # ---------------- 8. END-TO-END AI ENGINE PIPELINE ----------------
    print("\n[GROUP 8] Testing Anti-Hallucination AIEngine Pipeline...", flush=True)
    ai_engine = AIEngine()

    # Weather pipeline
    resp_weather = await ai_engine.process("How is the weather in London today?")
    assert len(resp_weather.tools_executed) == 1
    assert resp_weather.tools_executed[0].tool_name == "get_weather_forecast"
    assert resp_weather.tools_executed[0].is_verified is True
    print(" [PASS] AIEngine executed verified weather tool observation before LLM synthesis.", flush=True)

    # Currency pipeline
    resp_curr = await ai_engine.process("convert 100 USD to EUR")
    assert len(resp_curr.tools_executed) == 1
    assert resp_curr.tools_executed[0].tool_name == "convert_currency"
    assert resp_curr.tools_executed[0].is_verified is True
    print(" [PASS] AIEngine executed verified currency tool observation before LLM synthesis.", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("  ALL PUBLIC APIS INTEGRATION TESTS PASSED (100% SUCCESS)", flush=True)
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    t0 = time.perf_counter()
    asyncio.run(run_public_apis_tests())
    elapsed = round(time.perf_counter() - t0, 2)
    print(f"Suite completed in {elapsed}s.")
