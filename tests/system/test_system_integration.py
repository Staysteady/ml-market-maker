import pytest
import requests
import json
import time
from datetime import datetime, timedelta

def test_end_to_end_workflow(api_process, test_market_data):
    """Test complete system workflow."""
    base_url = api_process
    
    # 1. Deploy initial model
    deploy_response = requests.post(
        f"{base_url}/deploy",
        json={
            'version_id': 'v20230101_000000_test',
            'description': 'Initial deployment'
        }
    )
    assert deploy_response.status_code == 200
    assert deploy_response.json()['success']
    
    # 2. Get predictions
    predict_response = requests.post(
        f"{base_url}/predict",
        json={
            'instrument_id': 'section1',
            'bid_prices': [100.25, 100.50],
            'ask_prices': [100.50, 100.75]
        }
    )
    assert predict_response.status_code == 200
    prediction = predict_response.json()
    assert 'adjustments' in prediction
    assert 'latency_ms' in prediction
    
    # 3. Check metrics
    time.sleep(1)  # Wait for metrics to update
    metrics_response = requests.get(f"{base_url}/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert 'performance' in metrics
    assert 'health' in metrics
    
    # 4. Deploy new version
    deploy_response = requests.post(
        f"{base_url}/deploy",
        json={
            'version_id': 'v20230102_000000_test',
            'description': 'Updated model'
        }
    )
    assert deploy_response.status_code == 200
    
    # 5. Verify deployment
    status_response = requests.get(f"{base_url}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status['current_version'] == 'v20230102_000000_test'
    
    # 6. Test rollback
    rollback_response = requests.post(f"{base_url}/rollback")
    assert rollback_response.status_code == 200
    assert rollback_response.json()['success']
    
    # Verify rollback
    status_response = requests.get(f"{base_url}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status['current_version'] == 'v20230101_000000_test'

def test_error_handling(api_process):
    """Test system error handling."""
    base_url = api_process
    
    # Test invalid model version
    response = requests.post(
        f"{base_url}/deploy",
        json={
            'version_id': 'invalid_version',
            'description': 'Invalid deployment'
        }
    )
    assert response.status_code == 500
    
    # Test invalid market data
    response = requests.post(
        f"{base_url}/predict",
        json={
            'instrument_id': 'section1',
            'bid_prices': [],  # Empty prices
            'ask_prices': [100.50]
        }
    )
    assert response.status_code == 500

def test_monitoring_integration(api_process, system_components):
    """Test monitoring system integration."""
    base_url = api_process
    monitor = system_components['monitor']
    
    # Generate some load
    for _ in range(10):
        requests.post(
            f"{base_url}/predict",
            json={
                'instrument_id': 'section1',
                'bid_prices': [100.25],
                'ask_prices': [100.50]
            }
        )
        time.sleep(0.1)
    
    # Check metrics
    metrics_response = requests.get(f"{base_url}/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    
    # Verify metrics are being collected
    assert metrics['performance']['avg_latency'] > 0
    assert metrics['performance']['avg_throughput'] > 0
    assert 'avg_memory' in metrics['health']
    assert 'avg_cpu' in metrics['health']

def test_concurrent_requests(api_process):
    """Test system under concurrent load."""
    base_url = api_process
    import concurrent.futures
    
    def make_prediction():
        return requests.post(
            f"{base_url}/predict",
            json={
                'instrument_id': 'section1',
                'bid_prices': [100.25],
                'ask_prices': [100.50]
            }
        )
    
    # Make concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_prediction) for _ in range(10)]
        responses = [f.result() for f in futures]
    
    # Verify all requests succeeded
    assert all(r.status_code == 200 for r in responses)
    
    # Check system health after load
    status_response = requests.get(f"{base_url}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status['health_status'] == 'healthy'

def test_data_persistence(api_process, test_db):
    """Test data persistence across system components."""
    base_url = api_process
    
    # Make predictions
    prediction_response = requests.post(
        f"{base_url}/predict",
        json={
            'instrument_id': 'section1',
            'bid_prices': [100.25],
            'ask_prices': [100.50]
        }
    )
    prediction_id = prediction_response.json()['prediction_id']
    
    # Verify prediction was stored
    stored_prediction = test_db.get_prediction(prediction_id)
    assert stored_prediction is not None
    
    # Check metrics were stored
    metrics_response = requests.get(f"{base_url}/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert len(metrics['performance']['history']) > 0 