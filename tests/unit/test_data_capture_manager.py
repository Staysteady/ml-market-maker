import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, time
import pandas as pd
from src.data.capture.data_capture_manager import DataCaptureManager
from src.data.storage.database_manager import DatabaseManager

@pytest.fixture
def mock_config():
    return {
        'system': {
            'trading_hours': {
                'start': '07:00',
                'end': '16:00'
            },
            'capture_interval': 5,
            'stability_window': 4
        },
        'stability_tolerance': 0.25
    }

@pytest.fixture
def mock_reader():
    reader = MagicMock()
    reader.read_market_data.return_value = {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        }
    }
    return reader

@pytest.fixture
def mock_db_manager():
    return MagicMock(spec=DatabaseManager)

def test_trading_hours_check(mock_reader, mock_config):
    manager = DataCaptureManager(mock_reader, mock_config)
    
    # Test during trading hours
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.combine(
            datetime.today(),
            time(hour=10, minute=30)
        )
        assert manager._is_trading_hours() == True
        
    # Test outside trading hours
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.combine(
            datetime.today(),
            time(hour=18, minute=30)
        )
        assert manager._is_trading_hours() == False

def test_stability_check(mock_reader, mock_config):
    manager = DataCaptureManager(mock_reader, mock_config)
    
    # Test with stable data
    stable_data = {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        }
    }
    
    # Need multiple samples for stability
    assert manager._is_stable(stable_data) == False  # First sample
    assert manager._is_stable(stable_data) == False  # Second sample
    assert manager._is_stable(stable_data) == True   # Third sample - should be stable

def test_capture_loop_error_handling(mock_reader, mock_config):
    manager = DataCaptureManager(mock_reader, mock_config)
    
    # Make reader raise an exception
    mock_reader.read_market_data.side_effect = Exception("Test error")
    
    # Start capture
    manager.start_capture()
    time.sleep(0.1)  # Let it run briefly
    
    # Stop capture
    manager.stop_capture()
    
    # Should have logged the error
    # Note: Would need to capture logs to verify this properly 

def test_process_capture_stores_data(mock_reader, mock_config, mock_db_manager):
    """Test that processed captures are stored in database."""
    manager = DataCaptureManager(mock_reader, mock_config, mock_db_manager)
    
    test_data = {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        }
    }
    
    # Process the capture
    manager._process_capture(test_data)
    
    # Verify data was stored
    mock_db_manager.store_snapshot.assert_called_once_with(test_data)

def test_capture_loop_with_database(mock_reader, mock_config, mock_db_manager):
    """Test full capture loop with database integration."""
    manager = DataCaptureManager(mock_reader, mock_config, mock_db_manager)
    
    # Configure mock reader to return test data
    test_data = {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        }
    }
    mock_reader.read_market_data.return_value = test_data
    
    # Start capture
    with patch('datetime.datetime') as mock_dt:
        # Simulate being in trading hours
        mock_dt.now.return_value = datetime.combine(
            datetime.today(),
            time(hour=10, minute=30)
        )
        
        manager.start_capture()
        time.sleep(0.2)  # Let it run briefly
        manager.stop_capture()
    
    # Verify data was stored
    assert mock_db_manager.store_snapshot.called

def test_error_handling_with_database(mock_reader, mock_config, mock_db_manager):
    """Test error handling when database storage fails."""
    manager = DataCaptureManager(mock_reader, mock_config, mock_db_manager)
    
    # Make database storage raise an error
    mock_db_manager.store_snapshot.side_effect = Exception("Database error")
    
    test_data = {
        'section1': {
            'bid': pd.Series([100.25]),
            'ask': pd.Series([100.50])
        }
    }
    
    # Should not raise exception
    manager._process_capture(test_data)
    
    # Verify error was logged (would need log capture to verify properly) 