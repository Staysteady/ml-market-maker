import pandas as pd
import numpy as np
import pytest
import time
from unittest.mock import MagicMock
import tempfile

def test_validate_data_valid_input(config_path):
    reader = ExcelReader(config_path)
    
    # Create valid test data
    test_data = {
        'section1': {
            'bid': pd.Series([100.25, 100.50, 100.75]),
            'ask': pd.Series([100.50, 100.75, 101.00])
        },
        'section2': {
            'bid': pd.Series([50.25, 50.50]),
            'ask': pd.Series([50.50, 50.75])
        },
        'section3': {
            'bid': pd.Series([75.25, 75.50]),
            'ask': pd.Series([75.50, 75.75])
        }
    }
    
    assert reader.validate_data(test_data) == True

def test_validate_data_invalid_spread(config_path):
    reader = ExcelReader(config_path)
    
    # Create invalid test data where bid > ask
    test_data = {
        'section1': {
            'bid': pd.Series([100.50]),
            'ask': pd.Series([100.25])  # Invalid: ask < bid
        }
    }
    
    with pytest.raises(ValueError, match="Invalid bid-ask relationship"):
        reader.validate_data(test_data)

def test_validate_price_increments(config_path):
    reader = ExcelReader(config_path)
    
    # Invalid increment (0.3 instead of 0.25 or 0.5)
    test_data = {
        'section1': {
            'bid': pd.Series([100.30]),
            'ask': pd.Series([100.55])
        }
    }
    
    with pytest.raises(ValueError, match="Invalid bid price increments"):
        reader.validate_data(test_data)

def test_file_watching(config_path):
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        # Create test Excel file
        df = pd.DataFrame({
            'bid': [100.25, 100.50],
            'ask': [100.50, 100.75]
        })
        df.to_excel(tmp.name, index=False)
        
        reader = ExcelReader(config_path)
        reader.set_file_path(tmp.name)
        
        # Mock callback
        callback = MagicMock()
        reader.set_watch_callback(callback)
        
        # Start watching in a separate thread
        import threading
        watch_thread = threading.Thread(target=reader.start_watching, args=(0.1,))
        watch_thread.daemon = True
        watch_thread.start()
        
        # Modify file
        time.sleep(0.2)  # Wait for watcher to start
        df.loc[0, 'bid'] = 100.75
        df.to_excel(tmp.name, index=False)
        
        # Wait for callback
        time.sleep(0.3)
        
        # Stop watching
        reader.stop_watching()
        watch_thread.join(timeout=1.0)
        
        # Verify callback was called
        assert callback.called
        
        # Cleanup
        import os
        os.unlink(tmp.name)

def test_watch_without_callback(config_path):
    reader = ExcelReader(config_path)
    reader.set_file_path("test.xlsx")
    
    with pytest.raises(ValueError, match="Watch callback not set"):
        reader.start_watching()

def test_watch_without_file_path(config_path):
    reader = ExcelReader(config_path)
    callback = MagicMock()
    reader.set_watch_callback(callback)
    
    with pytest.raises(ValueError, match="File path not set"):
        reader.start_watching() 