import pytest
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from src.data.storage.database_manager import DatabaseManager

@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing."""
    db_path = tmp_path / "test.db"
    return str(db_path)

@pytest.fixture
def db_manager(temp_db):
    """Create database manager with temporary database."""
    manager = DatabaseManager(temp_db)
    yield manager
    manager.close()

def test_database_initialization(temp_db):
    """Test database is properly initialized."""
    manager = DatabaseManager(temp_db)
    
    # Check tables exist
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    assert 'market_snapshots' in tables
    assert 'instruments' in tables
    assert 'user_adjustments' in tables
    
    conn.close()

def test_store_snapshot(db_manager):
    """Test storing market data snapshot."""
    test_data = {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        }
    }
    
    db_manager.store_snapshot(test_data)
    
    # Verify data was stored
    df = db_manager.get_recent_data('section1', minutes=1)
    assert not df.empty
    assert 'bid_price' in df.columns
    assert 'ask_price' in df.columns
    assert 'mid_price' in df.columns

def test_get_recent_data(db_manager):
    """Test retrieving recent market data."""
    # Store some test data
    test_data = {
        'section1': {
            'bid': pd.Series([100.25]),
            'ask': pd.Series([100.50])
        }
    }
    
    # Store multiple snapshots
    for _ in range(3):
        db_manager.store_snapshot(test_data)
    
    # Get recent data
    df = db_manager.get_recent_data('section1', minutes=1)
    
    assert len(df) == 3
    assert (df['bid_price'] == 100.25).all()
    assert (df['ask_price'] == 100.50).all()

def test_store_user_adjustment(db_manager):
    """Test storing user price adjustments."""
    db_manager.store_user_adjustment(
        instrument_id='section1',
        old_mid=100.25,
        new_mid=100.50,
        reason='Test adjustment'
    )
    
    # Verify adjustment was stored
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_adjustments")
    row = cursor.fetchone()
    
    assert row is not None
    assert row['instrument_id'] == 'section1'
    assert row['old_mid'] == 100.25
    assert row['new_mid'] == 100.50
    assert row['reason'] == 'Test adjustment' 