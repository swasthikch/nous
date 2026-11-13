"""FastAPI REST Router for Financial Market Intelligence & Causal Reasoning."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.market.db import MarketDBManager
from backend.app.market.engine import MarketReasoningEngine
from backend.app.market.fetcher import MarketDataFetcher

logger = logging.getLogger("nous.api.market")

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])

# Singletons for fetcher, db, and engine
_db_manager = MarketDBManager()
_fetcher = MarketDataFetcher(db_manager=_db_manager)
_reasoning_engine = MarketReasoningEngine(fetcher=_fetcher)


# ---------------- REQUEST / RESPONSE SCHEMAS ----------------


class WatchlistAddRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol (e.g. ^NSEI, RELIANCE.NS, ^IXIC)")
    name: str = Field(..., description="Company or Index name")
    market: str = Field("NSE", description="Market identifier (NSE, BSE, US, FX, COMMODITY)")


class AlertCreateRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol")
    condition: str = Field(..., description="Alert condition (above, below, pct_up, pct_down, volume_surge)")
    target_value: float = Field(..., description="Numerical target threshold")
    notes: str = Field("", description="Optional user notes")


class AnalyzeRequest(BaseModel):
    symbol: str = Field("^NSEI", description="Symbol or index to analyze (e.g. ^NSEI, TCS.NS, RELIANCE.NS)")


# ---------------- ENDPOINTS ----------------


@router.get("/indices")
def get_benchmark_indices() -> dict[str, Any]:
    """Retrieve primary Indian and Global benchmark indices with market session statuses."""
    try:
        return _fetcher.get_benchmark_indices()
    except Exception as e:
        logger.error("Failed to retrieve market indices: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{symbol}")
def get_quote(symbol: str, refresh: bool = Query(False)) -> dict[str, Any]:
    """Retrieve real-time / cached quote for an instrument including intraday sparkline."""
    try:
        quote = _fetcher.fetch_quote(symbol, force_refresh=refresh)
        return quote
    except Exception as e:
        logger.error("Failed to fetch quote for %s: %s", symbol, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
def get_watchlist(with_quotes: bool = Query(True)) -> dict[str, Any]:
    """Retrieve user's personal watchlist, optionally enriched with current quotes."""
    try:
        items = _db_manager.get_watchlist()
        if with_quotes:
            symbols = [item["symbol"] for item in items]
            quotes = _fetcher.fetch_batch_quotes(symbols)
            quote_map = {q["symbol"].upper(): q for q in quotes}
            for it in items:
                it["quote"] = quote_map.get(it["symbol"].upper())
        return {"watchlist": items, "count": len(items)}
    except Exception as e:
        logger.error("Failed to get watchlist: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
def add_to_watchlist(req: WatchlistAddRequest) -> dict[str, Any]:
    """Add a new symbol to user watchlist."""
    try:
        added = _db_manager.add_to_watchlist(req.symbol, req.name, req.market)
        # Fetch initial quote to cache immediately
        _fetcher.fetch_quote(req.symbol, force_refresh=True)
        return {"status": "success", "item": added}
    except Exception as e:
        logger.error("Failed to add to watchlist: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str) -> dict[str, Any]:
    """Remove a symbol from user watchlist."""
    try:
        removed = _db_manager.remove_from_watchlist(symbol)
        if not removed:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in watchlist")
        return {"status": "success", "symbol": symbol.upper()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove symbol from watchlist: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
def get_alerts(active_only: bool = Query(False)) -> dict[str, Any]:
    """Retrieve market alerts."""
    try:
        alerts = _db_manager.get_alerts(only_active=active_only)
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error("Failed to retrieve alerts: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts")
def create_alert(req: AlertCreateRequest) -> dict[str, Any]:
    """Create a new threshold alert for an instrument."""
    try:
        alert = _db_manager.add_alert(
            symbol=req.symbol,
            condition=req.condition,
            target_value=req.target_value,
            notes=req.notes,
        )
        return {"status": "success", "alert": alert}
    except Exception as e:
        logger.error("Failed to create alert: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: str) -> dict[str, Any]:
    """Delete an alert by ID."""
    try:
        deleted = _db_manager.delete_alert(alert_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "success", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete alert: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
def analyze_market_movement(req: AnalyzeRequest) -> dict[str, Any]:
    """Execute Phase 11 Causal Reasoning to explain why an index or stock moved."""
    try:
        analysis = _reasoning_engine.analyze_movement(req.symbol)
        report = _reasoning_engine.generate_formatted_report(req.symbol)
        return {
            "status": "success",
            "analysis": analysis,
            "formatted_report": report,
        }
    except Exception as e:
        logger.error("Failed to analyze market movement for %s: %s", req.symbol, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fii-dii")
def get_fii_dii_activity() -> dict[str, Any]:
    """Retrieve institutional investment activity (FII and DII flows)."""
    try:
        return _fetcher.get_fii_dii_flows()
    except Exception as e:
        logger.error("Failed to get FII/DII data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
