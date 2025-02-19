import pytest
from datetime import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import shutil

from src.models.deployment.deployment_manager import DeploymentManager

@pytest.fixture
def deployment_config():
    return {
        'deployment': {
            'base_dir': 'deployments',
            'status_window_hours': 24,
            'min_memory_mb': 1024,
            'max_cpu_percent': 80,
            'requirements': {
                'accuracy': 0.8,
                'latency_ms': 100
            }
        }
    }

@pytest.fixture
def mock_version_manager():
    manager = MagicMock()
    manager.get_version_info.return_value = {
        'metrics': {
            'accuracy': 0.9,
            'latency_ms': 50
        }
    }
    return manager

@pytest.fixture
def mock_model_server():
    server = MagicMock()
    server.current_model_version = 'v20230101_000000_test'
    server.update_model.return_value = True
    return server

@pytest.fixture
def mock_model_monitor():
    monitor = MagicMock()
    monitor.get_metrics_summary.return_value = {
        'performance': {
            'avg_latency': 50,
            'avg_throughput': 100,
            'avg_error_rate': 0.01
        },
        'health': {
            'avg_memory': 500,
            'avg_cpu': 50
        }
    }
    monitor.check_alerts.return_value = []
    return monitor

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def deployment_manager(
    deployment_config,
    mock_version_manager,
    mock_model_server,
    mock_model_monitor,
    mock_db_manager,
    tmp_path
):
    deployment_config['deployment']['base_dir'] = str(tmp_path)
    return DeploymentManager(
        mock_version_manager,
        mock_model_server,
        mock_model_monitor,
        mock_db_manager,
        deployment_config
    )

def test_deploy_model(deployment_manager):
    success = deployment_manager.deploy_model(
        'v20230101_000000_test',
        'Test deployment'
    )
    
    assert success
    assert len(deployment_manager.deployment_history) == 1
    assert deployment_manager.deployment_history[0]['version_id'] == 'v20230101_000000_test'

def test_deploy_model_dry_run(deployment_manager):
    success = deployment_manager.deploy_model(
        'v20230101_000000_test',
        'Test deployment',
        dry_run=True
    )
    
    assert success
    assert len(deployment_manager.deployment_history) == 0

def test_rollback_deployment(deployment_manager):
    # Deploy initial version
    deployment_manager.deploy_model(
        'v20230101_000000_test',
        'Initial deployment'
    )
    
    # Deploy another version
    deployment_manager.deploy_model(
        'v20230102_000000_test',
        'Second deployment'
    )
    
    # Rollback
    success = deployment_manager.rollback_deployment()
    
    assert success
    assert deployment_manager.model_server.current_model_version == 'v20230101_000000_test'

def test_deployment_status(deployment_manager):
    deployment_manager.deploy_model(
        'v20230101_000000_test',
        'Test deployment'
    )
    
    status = deployment_manager.get_deployment_status()
    
    assert status['current_version'] == 'v20230101_000000_test'
    assert 'metrics' in status
    assert 'alerts' in status
    assert status['health_status'] == 'healthy'

@patch('psutil.virtual_memory')
@patch('psutil.cpu_percent')
def test_resource_checks(mock_cpu, mock_memory, deployment_manager):
    # Mock sufficient resources
    mock_memory.return_value.available = 2 * 1024 * 1024 * 1024  # 2GB
    mock_cpu.return_value = 50
    
    assert deployment_manager._check_resources()
    
    # Mock insufficient resources
    mock_memory.return_value.available = 512 * 1024 * 1024  # 512MB
    mock_cpu.return_value = 90
    
    assert not deployment_manager._check_resources()

def test_deployment_history_persistence(deployment_manager, tmp_path):
    # Deploy a model
    deployment_manager.deploy_model(
        'v20230101_000000_test',
        'Test deployment'
    )
    
    # Check history was saved
    history_file = tmp_path / 'deployment_history.json'
    assert history_file.exists()
    
    # Verify content
    with open(history_file, 'r') as f:
        saved_history = json.load(f)
        assert len(saved_history) == 1
        assert saved_history[0]['version_id'] == 'v20230101_000000_test' 