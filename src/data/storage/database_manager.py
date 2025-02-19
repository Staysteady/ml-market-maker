import logging
from typing import Dict, Any, Optional, List
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

from .schema import initialize_database

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles database operations and connection management."""
    
    def __init__(self, db_path: str):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_db_directory()
        self.connection: Optional[sqlite3.Connection] = None
        self._setup_database()
        
    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _setup_database(self) -> None:
        """Initialize database and create tables if needed."""
        initialize_database(str(self.db_path))
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating if needed."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection
        
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def store_snapshot(self, data: Dict[str, Any]) -> None:
        """Store market data snapshot.
        
        Args:
            data: Market data dictionary
        """
        try:
            conn = self._get_connection()
            timestamp = datetime.now()
            
            with conn:  # Automatic transaction
                for section_name, section_data in data.items():
                    if isinstance(section_data, dict):  # bid/ask section
                        self._store_bid_ask_data(
                            conn, timestamp, section_name, section_data)
                    else:  # midpoint section
                        self._store_midpoint_data(
                            conn, timestamp, section_name, section_data)
                            
            logger.debug(f"Stored snapshot at {timestamp}")
            
        except Exception as e:
            logger.error(f"Failed to store snapshot: {e}")
            raise
            
    def _store_bid_ask_data(
        self, 
        conn: sqlite3.Connection, 
        timestamp: datetime,
        instrument_id: str,
        data: Dict[str, pd.Series]
    ) -> None:
        """Store bid/ask data for an instrument."""
        for bid, ask in zip(data['bid'], data['ask']):
            mid = (bid + ask) / 2
            conn.execute(
                """
                INSERT INTO market_snapshots 
                (timestamp, instrument_id, bid_price, ask_price, mid_price, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, instrument_id, bid, ask, mid, 'excel')
            )
            
    def _store_midpoint_data(
        self,
        conn: sqlite3.Connection,
        timestamp: datetime,
        instrument_id: str,
        data: pd.Series
    ) -> None:
        """Store midpoint data for an instrument."""
        for mid in data:
            conn.execute(
                """
                INSERT INTO market_snapshots 
                (timestamp, instrument_id, mid_price, source)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, instrument_id, mid, 'excel')
            )
            
    def get_recent_data(
        self,
        instrument_id: str,
        minutes: int = 5
    ) -> pd.DataFrame:
        """Retrieve recent market data for analysis.
        
        Args:
            instrument_id: Instrument identifier
            minutes: Number of minutes of historical data to retrieve
            
        Returns:
            DataFrame containing recent market data
        """
        try:
            conn = self._get_connection()
            since = datetime.now() - timedelta(minutes=minutes)
            
            query = """
            SELECT * FROM market_snapshots
            WHERE instrument_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            """
            
            df = pd.read_sql_query(
                query,
                conn,
                params=(instrument_id, since),
                parse_dates=['timestamp']
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent data: {e}")
            raise
            
    def store_user_adjustment(
        self,
        instrument_id: str,
        old_mid: float,
        new_mid: float,
        reason: Optional[str] = None
    ) -> None:
        """Store user price adjustment.
        
        Args:
            instrument_id: Instrument identifier
            old_mid: Previous mid price
            new_mid: New mid price
            reason: Optional reason for adjustment
        """
        try:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    """
                    INSERT INTO user_adjustments
                    (timestamp, instrument_id, old_mid, new_mid, reason)
                    VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?)
                    """,
                    (instrument_id, old_mid, new_mid, reason)
                )
                
            logger.info(f"Stored user adjustment for {instrument_id}")
            
        except Exception as e:
            logger.error(f"Failed to store user adjustment: {e}")
            raise 