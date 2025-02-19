import pytest
from datetime import datetime
import numpy as np
from unittest.mock import MagicMock, patch
import time
import threading
import json

from src.models.serving.model_server import ModelServer
from src.models.agents.price_agent import PriceAgent

@pytest.fixture
def server_config():
    return {
        'model': {
            'input_size': 24,
            'hidden_size': 64,
            'output_size': 4,
            'max_adjustment': 0.5
        },
        'serving': {
            'queue_size': 100,
            'max_delay': 1.0
        }
    }

@pytest.fixture
def mock_version_manager(tmp_path):
    manager = MagicMock()
    
    # Set up mock active version
    version_id = 'v20230101_000000_test'
    active_dir = tmp_path / 'active' / version_id
    active_dir.mkdir(parents=True)
    
    # Create mock model files
    model = PriceAgent(server_config())
    model.save(str(active_dir / 'model.pt'))
    
    with open(active_dir / 'metadata.json', 'w') as f:
        json.dump({
            'config': server_config(),
            'version_id': version_id
        }, f)
        
    manager.get_active_version.return_value = version_id
    manager.active_dir = tmp_path / 'active'
    
    return manager

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def model_server(server_config, mock_version_manager, mock_db_manager):
    server = ModelServer(
        mock_version_manager,
        mock_db_manager,
        server_config
    )
    yield server
    server.shutdown()

def test_server_initialization(model_server):
    assert model_server.current_model is not None
    assert model_server.is_running
    assert model_server.worker_thread.is_alive()

def test_synchronous_prediction(model_server):
    market_state = {
        'section1': {
            'bid': np.array([100.25]),
            'ask': np.array([100.50])
        }
    }
    
    prediction = model_server.predict(market_state)
    
    assert isinstance(prediction, dict)
    assert 'section1' in prediction
    assert isinstance(prediction['section1'], float)

def test_async_prediction(model_server):
    market_state = {
        'section1': {
            'bid': np.array([100.25]),
            'ask': np.array([100.50])
        }
    }
    
    # Submit async prediction
    result = model_server.predict(market_state, async_mode=True)
    assert result is None
    
    # Wait for processing
    time.sleep(0.1)
    
    # Verify prediction was stored
    mock_db_manager.store_prediction.assert_called_once()

def test_model_update(model_server, mock_version_manager):
    # Create new version
    new_version = 'v20230102_000000_test'
    
    # Update to new version
    success = model_server.update_model(new_version)
    
    assert success
    assert model_server.current_model_version == new_version

def test_server_shutdown(model_server):
    model_server.shutdown()
    
    assert not model_server.is_running
    assert not model_server.worker_thread.is_alive() 