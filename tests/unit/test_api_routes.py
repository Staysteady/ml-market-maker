import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.api.routes import router, get_deployment_manager, get_model_server, get_model_monitor

# Mock dependencies
@pytest.fixture
def mock_deployment_manager():
    manager = MagicMock()
    manager.deploy_model.return_value = True
    manager.rollback_deployment.return_value = True
    manager.get_deployment_status.return_value = {
        'current_version': 'v20230101_000000_test',
        'deployment_time': datetime.now().isoformat(),
        'metrics': {},
        'alerts': [],
        'health_status': 'healthy'
    }
    return manager

@pytest.fixture
def mock_model_server():
    server = MagicMock()
    server.predict.return_value = {'section1': 0.25}
    server.current_model_version = 'v20230101_000000_test'
    return server

@pytest.fixture
def mock_model_monitor():
    monitor = MagicMock()
    monitor.get_metrics_summary.return_value = {
        'performance': {'avg_latency': 50},
        'health': {'avg_memory': 500}
    }
    monitor.check_alerts.return_value = []
    return monitor

@pytest.fixture
def client(
    mock_deployment_manager,
    mock_model_server,
    mock_model_monitor
):
    # Override dependency injection
    app = TestClient(router)
    app.dependency_overrides[get_deployment_manager] = lambda: mock_deployment_manager
    app.dependency_overrides[get_model_server] = lambda: mock_model_server
    app.dependency_overrides[get_model_monitor] = lambda: mock_model_monitor
    return app

def test_predict_endpoint(client):
    response = client.post(
        "/predict",
        json={
            'instrument_id': 'section1',
            'bid_prices': [100.25],
            'ask_prices': [100.50]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'adjustments' in data
    assert 'model_version' in data
    assert 'prediction_id' in data
    assert 'latency_ms' in data

def test_deploy_endpoint(client):
    response = client.post(
        "/deploy",
        json={
            'version_id': 'v20230101_000000_test',
            'description': 'Test deployment'
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['success']
    assert 'deployment_id' in data

def test_rollback_endpoint(client):
    response = client.post("/rollback?steps=1")
    
    assert response.status_code == 200
    data = response.json()
    assert data['success']

def test_status_endpoint(client):
    response = client.get("/status")
    
    assert response.status_code == 200
    data = response.json()
    assert 'current_version' in data
    assert 'health_status' in data

def test_metrics_endpoint(client):
    response = client.get("/metrics?window_hours=24")
    
    assert response.status_code == 200
    data = response.json()
    assert 'performance' in data
    assert 'health' in data
    assert 'alerts' in data

def test_versions_endpoint(client):
    response = client.get("/versions")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_error_handling(client, mock_model_server):
    # Make server raise an error
    mock_model_server.predict.side_effect = Exception("Test error")
    
    response = client.post(
        "/predict",
        json={
            'instrument_id': 'section1',
            'bid_prices': [100.25],
            'ask_prices': [100.50]
        }
    )
    
    assert response.status_code == 500
    assert "Test error" in response.json()['detail'] 