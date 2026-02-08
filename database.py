"""Database operations for grain price storage."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "grain_prices.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grain_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            commodity TEXT NOT NULL,
            cash_price REAL,
            basis REAL,
            futures_change REAL,
            delivery_start TEXT,
            delivery_end TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON grain_prices(timestamp)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity ON grain_prices(commodity)
    """)

    conn.commit()
    conn.close()


def insert_price(
    commodity: str,
    cash_price: Optional[float],
    basis: Optional[float],
    futures_change: Optional[float],
    delivery_start: Optional[str],
    delivery_end: Optional[str],
    timestamp: Optional[datetime] = None
) -> int:
    """Insert a grain price record."""
    if timestamp is None:
        timestamp = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO grain_prices
        (timestamp, commodity, cash_price, basis, futures_change, delivery_start, delivery_end)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp.isoformat(), commodity, cash_price, basis, futures_change,
          delivery_start, delivery_end))

    row_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return row_id


def insert_prices(prices: list[dict], timestamp: Optional[datetime] = None) -> int:
    """Insert multiple grain price records."""
    if timestamp is None:
        timestamp = datetime.now()

    conn = get_connection()
    cursor = conn.cursor()

    count = 0
    for price in prices:
        cursor.execute("""
            INSERT INTO grain_prices
            (timestamp, commodity, cash_price, basis, futures_change, delivery_start, delivery_end)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp.isoformat(),
            price.get('commodity'),
            price.get('cash_price'),
            price.get('basis'),
            price.get('futures_change'),
            price.get('delivery_start'),
            price.get('delivery_end')
        ))
        count += 1

    conn.commit()
    conn.close()

    return count


def get_latest_prices() -> list[dict]:
    """Get the most recent prices for each commodity."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM grain_prices
        WHERE timestamp = (SELECT MAX(timestamp) FROM grain_prices)
        ORDER BY commodity
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_price_history(
    commodity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[dict]:
    """Get price history with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM grain_prices WHERE 1=1"
    params = []

    if commodity:
        query += " AND commodity = ?"
        params.append(commodity)

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date.isoformat())

    query += " ORDER BY timestamp DESC, commodity"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_commodities() -> list[str]:
    """Get list of all commodities in database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT commodity FROM grain_prices ORDER BY commodity")
    rows = cursor.fetchall()
    conn.close()

    return [row['commodity'] for row in rows]


# Initialize database on import
init_db()
