import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.data.capture.data_collector import DataCollector

@pytest.fixture
def mock_db_manager():
    manager = MagicMock()
    
    # Mock snapshot data
    snapshots = pd.DataFrame({
        'timestamp': [datetime.now()] * 4,
        'instrument_id': ['section1', 'section1', 'section2', 'section2'],
        'bid_price': [100.25, 100.50, 50.25, 50.50],
        'ask_price': [100.50, 100.75, 50.50, 50.75]
    })
    
    # Mock adjustment data
    adjustments = pd.DataFrame({
        'timestamp': [datetime.now()],
        'instrument_id': ['section1'],
        'old_mid': [100.25],
        'new_mid': [100.50]
    })
    
    # Mock read_sql_query to return appropriate data
    def mock_read_sql(*args, **kwargs):
        if 'market_snapshots' in args[0]:
            return snapshots
        elif 'user_adjustments' in args[0]:
            return adjustments
    
    manager._get_connection().cursor = MagicMock()
    pd.read_sql_query = MagicMock(side_effect=mock_read_sql)
    
    return manager

@pytest.fixture
def collector_config():
    return {
        'data_collection': {
            'batch_size': 32,
            'window_size': 10
        }
    }

def test_get_training_data(mock_db_manager, collector_config):
    collector = DataCollector(mock_db_manager, collector_config)
    
    market_states, user_adjustments = collector.get_training_data()
    
    # Check market states
    assert isinstance(market_states, list)
    assert all(isinstance(state, dict) for state in market_states)
    
    # Check user adjustments
    assert isinstance(user_adjustments, dict)
    assert all(isinstance(adj, list) for adj in user_adjustments.values())

def test_process_snapshots(mock_db_manager, collector_config):
    collector = DataCollector(mock_db_manager, collector_config)
    
    snapshots = pd.DataFrame({
        'timestamp': [datetime.now()] * 4,
        'instrument_id': ['section1', 'section1', 'section2', 'section2'],
        'bid_price': [100.25, 100.50, 50.25, 50.50],
        'ask_price': [100.50, 100.75, 50.50, 50.75]
    })
    
    market_states = collector._process_snapshots(snapshots)
    
    assert len(market_states) > 0
    assert all('bid' in state['section1'] for state in market_states)
    assert all('ask' in state['section1'] for state in market_states)

def test_process_adjustments(mock_db_manager, collector_config):
    collector = DataCollector(mock_db_manager, collector_config)
    
    adjustments = pd.DataFrame({
        'timestamp': [datetime.now()],
        'instrument_id': ['section1'],
        'old_mid': [100.25],
        'new_mid': [100.50]
    })
    
    adj_dict = collector._process_adjustments(adjustments)
    
    assert 'section1' in adj_dict
    assert len(adj_dict['section1']) > 0
    assert adj_dict['section1'][0] == 0.25  # new_mid - old_mid 