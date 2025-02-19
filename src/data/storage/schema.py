from typing import List
import sqlite3
import logging

logger = logging.getLogger(__name__)

SCHEMA_STATEMENTS: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS market_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        instrument_id TEXT NOT NULL,
        bid_price REAL,
        ask_price REAL,
        mid_price REAL,
        source TEXT NOT NULL,
        UNIQUE(timestamp, instrument_id)
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS instruments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price_increment REAL NOT NULL,
        active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS user_adjustments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        instrument_id TEXT NOT NULL,
        old_mid REAL,
        new_mid REAL,
        reason TEXT,
        FOREIGN KEY(instrument_id) REFERENCES instruments(id)
    )
    """,
    
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_time 
    ON market_snapshots(timestamp)
    """,
    
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_instrument 
    ON market_snapshots(instrument_id)
    """
]

def initialize_database(db_path: str) -> None:
    """Initialize database with schema.
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        with sqlite3.connect(db_path) as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.commit()
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise 