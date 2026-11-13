"""Database schema and management for NOUS Financial Market Intelligence."""

from __future__ import annotations

import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from backend.app.config import settings

# Default database path from config
DEFAULT_DB_PATH: Path = settings.MARKET_DB_PATH

# Seed watchlist for Indian and International markets
DEFAULT_SEED_WATCHLIST: list[dict] = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "market": "NSE", "display_order": 1},
    {"symbol": "^BSESN", "name": "S&P BSE SENSEX", "market": "BSE", "display_order": 2},
    {"symbol": "^NSEBANK", "name": "NIFTY Bank", "market": "NSE", "display_order": 3},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "market": "NSE", "display_order": 4},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "market": "NSE", "display_order": 5},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "market": "NSE", "display_order": 6},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "market": "US", "display_order": 7},
    {"symbol": "^GSPC", "name": "S&P 500", "market": "US", "display_order": 8},
    {"symbol": "INR=X", "name": "USD / INR", "market": "FX", "display_order": 9},
    {"symbol": "CL=F", "name": "Crude Oil (WTI)", "market": "COMMODITY", "display_order": 10},
]


def init_market_db(db_path: Path | None = None) -> Path:
    """Initialize the SQLite database for market data with WAL mode and tables."""
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")

        # Table: Watchlist
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_watchlist (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                added_at REAL NOT NULL
            );
            """
        )

        # Table: Alerts
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_alerts (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                condition TEXT NOT NULL,
                target_value REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                triggered_at REAL,
                created_at REAL NOT NULL,
                notes TEXT
            );
            """
        )

        # Table: Quotes Cache (with sparkline data points)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_quotes_cache (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                price REAL NOT NULL,
                change REAL NOT NULL,
                pct_change REAL NOT NULL,
                prev_close REAL NOT NULL,
                open_price REAL,
                day_high REAL,
                day_low REAL,
                volume INTEGER,
                currency TEXT,
                market_state TEXT,
                last_updated REAL NOT NULL,
                is_live INTEGER DEFAULT 1,
                sparkline_json TEXT
            );
            """
        )

        # Seed initial watchlist if empty
        cur = conn.execute("SELECT COUNT(*) FROM market_watchlist;")
        count = cur.fetchone()[0]
        if count == 0:
            now = time.time()
            for item in DEFAULT_SEED_WATCHLIST:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO market_watchlist (symbol, name, market, display_order, added_at)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (item["symbol"], item["name"], item["market"], item["display_order"], now),
                )
            conn.commit()

    return path


@contextmanager
def get_db(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding a SQLite connection with Row factory."""
    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        init_market_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class MarketDBManager:
    """Manages persistent market watchlist, alerts, and cached quotes."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        init_market_db(self.db_path)

    # ---------------- WATCHLIST OPERATIONS ----------------

    def get_watchlist(self) -> list[dict]:
        """Fetch all watched market instruments sorted by display order."""
        with get_db(self.db_path) as conn:
            cur = conn.execute(
                """
                SELECT symbol, name, market, display_order, added_at
                FROM market_watchlist
                ORDER BY display_order ASC, symbol ASC;
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def add_to_watchlist(self, symbol: str, name: str, market: str) -> dict:
        """Add an instrument to the personal watchlist."""
        sym = symbol.strip().upper()
        now = time.time()
        with get_db(self.db_path) as conn:
            # find max order
            cur = conn.execute("SELECT COALESCE(MAX(display_order), 0) + 1 FROM market_watchlist;")
            next_order = cur.fetchone()[0]
            conn.execute(
                """
                INSERT INTO market_watchlist (symbol, name, market, display_order, added_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name = excluded.name,
                    market = excluded.market;
                """,
                (sym, name.strip(), market.strip().upper(), next_order, now),
            )
        return {"symbol": sym, "name": name, "market": market, "added_at": now}

    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove an instrument from the watchlist."""
        sym = symbol.strip().upper()
        with get_db(self.db_path) as conn:
            cur = conn.execute("DELETE FROM market_watchlist WHERE UPPER(symbol) = ?;", (sym,))
            return cur.rowcount > 0

    # ---------------- ALERTS OPERATIONS ----------------

    def get_alerts(self, only_active: bool = False) -> list[dict]:
        """Fetch alerts with optional filtering for active alerts."""
        query = "SELECT * FROM market_alerts"
        params: list[object] = []
        if only_active:
            query += " WHERE is_active = 1"
        query += " ORDER BY created_at DESC;"

        with get_db(self.db_path) as conn:
            cur = conn.execute(query, params)
            rows = [dict(row) for row in cur.fetchall()]
            for r in rows:
                r["is_active"] = bool(r["is_active"])
            return rows

    def add_alert(
        self,
        symbol: str,
        condition: str,
        target_value: float,
        notes: str = "",
    ) -> dict:
        """Create a new threshold alert for an instrument."""
        alert_id = str(uuid.uuid4())
        now = time.time()
        sym = symbol.strip().upper()
        cond = condition.strip().lower()

        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_alerts (id, symbol, condition, target_value, is_active, created_at, notes)
                VALUES (?, ?, ?, ?, 1, ?, ?);
                """,
                (alert_id, sym, cond, target_value, now, notes),
            )

        return {
            "id": alert_id,
            "symbol": sym,
            "condition": cond,
            "target_value": target_value,
            "is_active": True,
            "created_at": now,
            "notes": notes,
        }

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert by ID."""
        with get_db(self.db_path) as conn:
            cur = conn.execute("DELETE FROM market_alerts WHERE id = ?;", (alert_id,))
            return cur.rowcount > 0

    def mark_alert_triggered(self, alert_id: str) -> bool:
        """Mark an alert as triggered and deactivate it."""
        now = time.time()
        with get_db(self.db_path) as conn:
            cur = conn.execute(
                """
                UPDATE market_alerts
                SET is_active = 0, triggered_at = ?
                WHERE id = ?;
                """,
                (now, alert_id),
            )
            return cur.rowcount > 0

    # ---------------- QUOTES CACHE OPERATIONS ----------------

    def save_cached_quote(self, quote: dict) -> None:
        """Upsert a quote into the quotes cache table."""
        now = time.time()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_quotes_cache (
                    symbol, name, price, change, pct_change, prev_close,
                    open_price, day_high, day_low, volume, currency,
                    market_state, last_updated, is_live, sparkline_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name = excluded.name,
                    price = excluded.price,
                    change = excluded.change,
                    pct_change = excluded.pct_change,
                    prev_close = excluded.prev_close,
                    open_price = excluded.open_price,
                    day_high = excluded.day_high,
                    day_low = excluded.day_low,
                    volume = excluded.volume,
                    currency = excluded.currency,
                    market_state = excluded.market_state,
                    last_updated = excluded.last_updated,
                    is_live = excluded.is_live,
                    sparkline_json = excluded.sparkline_json;
                """,
                (
                    quote["symbol"].upper(),
                    quote.get("name", quote["symbol"]),
                    quote["price"],
                    quote["change"],
                    quote["pct_change"],
                    quote.get("prev_close", 0.0),
                    quote.get("open_price"),
                    quote.get("day_high"),
                    quote.get("day_low"),
                    quote.get("volume", 0),
                    quote.get("currency", "INR"),
                    quote.get("market_state", "REGULAR"),
                    now,
                    1 if quote.get("is_live", True) else 0,
                    quote.get("sparkline_json", "[]"),
                ),
            )

    def get_cached_quote(self, symbol: str) -> dict | None:
        """Retrieve a cached quote by symbol."""
        sym = symbol.strip().upper()
        with get_db(self.db_path) as conn:
            cur = conn.execute("SELECT * FROM market_quotes_cache WHERE UPPER(symbol) = ?;", (sym,))
            row = cur.fetchone()
            if not row:
                return None
            res = dict(row)
            res["is_live"] = bool(res["is_live"])
            return res

    def get_all_cached_quotes(self) -> list[dict]:
        """Retrieve all currently cached quotes."""
        with get_db(self.db_path) as conn:
            cur = conn.execute("SELECT * FROM market_quotes_cache ORDER BY symbol ASC;")
            rows = [dict(row) for row in cur.fetchall()]
            for r in rows:
                r["is_live"] = bool(r["is_live"])
            return rows
