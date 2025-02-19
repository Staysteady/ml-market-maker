import pytest
import os
import subprocess
import time
import requests
from pathlib import Path
import json
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.models.deployment.deployment_manager import DeploymentManager
from src.models.serving.model_server import ModelServer
from src.models.monitoring.monitor import ModelMonitor
from src.data.storage.database_manager import DatabaseManager

@pytest.fixture(scope="session")
def test_config():
    return {
        'model': {
            'input_size': 24,
            'hidden_size': 64,
            'output_size': 4,
            'max_adjustment': 0.5
        },
        'training': {
            'learning_rate': 0.001,
            'batch_size': 32,
            'spread_weight': 0.1
        },
        'deployment': {
            'base_dir': 'test_deployments',
            'min_memory_mb': 512,
            'max_cpu_percent': 80
        },
        'monitoring': {
            'metrics_window_minutes': 60,
            'alert_window_hours': 24
        },
        'serving': {
            'queue_size': 100,
            'max_delay': 1.0
        }
    }

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    db_path = Path("test_data.db")
    if db_path.exists():
        db_path.unlink()
        
    db_manager = DatabaseManager(str(db_path))
    db_manager.initialize_database()
    
    yield db_manager
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()

@pytest.fixture(scope="session")
def api_process():
    """Start API server for testing."""
    server = subprocess.Popen(
        ["uvicorn", "src.api.routes:router", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    
    yield "http://localhost:8001"
    
    # Cleanup
    server.terminate()
    server.wait()

@pytest.fixture
def test_market_data():
    """Generate test market data."""
    return {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        },
        'section2': {
            'bid': pd.Series([50.25, 50.50]),
            'ask': pd.Series([50.50, 50.75])
        }
    }

@pytest.fixture
def system_components(test_config, test_db):
    """Initialize system components."""
    model_server = ModelServer(None, test_db, test_config)
    model_monitor = ModelMonitor(test_db, test_config)
    deployment_manager = DeploymentManager(
        None, model_server, model_monitor, test_db, test_config
    )
    
    return {
        'server': model_server,
        'monitor': model_monitor,
        'deployment': deployment_manager
    } 