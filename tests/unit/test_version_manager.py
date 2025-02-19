import pytest
from datetime import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import torch

from src.models.versioning.version_manager import ModelVersionManager
from src.models.agents.price_agent import PriceAgent

@pytest.fixture
def version_config():
    return {
        'model': {
            'input_size': 24,
            'hidden_size': 64,
            'output_size': 4,
            'max_adjustment': 0.5
        }
    }

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def version_manager(version_config, mock_db_manager, tmp_path):
    return ModelVersionManager(
        str(tmp_path),
        mock_db_manager,
        version_config
    )

@pytest.fixture
def test_model(version_config):
    return PriceAgent(version_config)

def test_register_model(version_manager, test_model):
    metrics = {
        'profitable_adjustments': 0.8,
        'mean_spread_impact': 0.1
    }
    
    version_id = version_manager.register_model(
        test_model,
        metrics,
        "Test model version",
        tags=['test']
    )
    
    assert version_id is not None
    version_dir = version_manager.models_dir / version_id
    assert version_dir.exists()
    assert (version_dir / 'model.pt').exists()
    assert (version_dir / 'metadata.json').exists()

def test_activate_version(version_manager, test_model):
    # Register a model
    version_id = version_manager.register_model(
        test_model,
        {'test_metric': 1.0},
        "Test activation"
    )
    
    # Activate it
    version_manager.activate_version(version_id)
    
    # Check it's active
    assert version_manager.get_active_version() == version_id
    assert (version_manager.active_dir / version_id).exists()

def test_version_filtering(version_manager, test_model):
    # Register multiple versions
    version_manager.register_model(
        test_model,
        {'accuracy': 0.8},
        "High accuracy model",
        tags=['accurate']
    )
    version_manager.register_model(
        test_model,
        {'accuracy': 0.6},
        "Fast model",
        tags=['fast']
    )
    
    # Filter by tags
    accurate_versions = version_manager.list_versions(tags=['accurate'])
    assert len(accurate_versions) == 1
    assert accurate_versions[0]['tags'] == ['accurate']
    
    # Filter by metrics
    good_versions = version_manager.list_versions(
        metric_threshold={'accuracy': 0.7}
    )
    assert len(good_versions) == 1
    assert good_versions[0]['metrics']['accuracy'] >= 0.7

def test_version_info(version_manager, test_model):
    # Register a model
    version_id = version_manager.register_model(
        test_model,
        {'test_metric': 1.0},
        "Test version info"
    )
    
    # Get version info
    info = version_manager.get_version_info(version_id)
    
    assert info is not None
    assert info['version_id'] == version_id
    assert 'timestamp' in info
    assert 'metrics' in info
    assert 'description' in info 