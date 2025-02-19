import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
import json

from src.models.monitoring.monitor import ModelMonitor, PerformanceMetrics, HealthMetrics

@pytest.fixture
def monitor_config():
    return {
        'monitoring': {
            'metrics_window_minutes': 60,
            'alert_window_hours': 24,
            'max_latency_ms': 100,
            'max_error_rate': 0.05,
            'max_memory_mb': 1024,
            'max_cpu_percent': 80
        },
        'serving': {
            'queue_size': 100
        }
    }

@pytest.fixture
def mock_db_manager():
    manager = MagicMock()
    
    # Mock prediction data
    predictions = pd.DataFrame({
        'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(10)],
        'latency_ms': np.random.uniform(10, 90, 10),
        'error': [0] * 9 + [1],  # 10% error rate
        'queue_size': np.random.randint(0, 100, 10),
        'accuracy': np.random.uniform(0.8, 1.0, 10),
        'spread_compliant': [1] * 8 + [0] * 2  # 80% compliance
    })
    
    manager._get_connection().cursor = MagicMock()
    pd.read_sql_query = MagicMock(return_value=predictions)
    
    return manager

@pytest.fixture
def model_monitor(monitor_config, mock_db_manager, tmp_path):
    return ModelMonitor(
        mock_db_manager,
        monitor_config,
        metrics_dir=str(tmp_path)
    )

def test_performance_metrics_collection(model_monitor):
    metrics = model_monitor.collect_performance_metrics()
    
    assert isinstance(metrics, PerformanceMetrics)
    assert 0 <= metrics.error_rate <= 1
    assert metrics.prediction_latency > 0
    assert metrics.prediction_throughput >= 0
    assert 0 <= metrics.queue_utilization <= 1
    assert 0 <= metrics.prediction_accuracy <= 1
    assert 0 <= metrics.spread_compliance <= 1

@patch('psutil.Process')
def test_health_metrics_collection(mock_process, model_monitor):
    mock_process.return_value.memory_info.return_value.rss = 500 * 1024 * 1024
    mock_process.return_value.cpu_percent.return_value = 50
    
    metrics = model_monitor.collect_health_metrics()
    
    assert isinstance(metrics, HealthMetrics)
    assert metrics.memory_usage > 0
    assert 0 <= metrics.cpu_usage <= 100
    assert metrics.queue_size >= 0
    assert metrics.active_threads > 0
    assert metrics.uptime >= 0

def test_metrics_summary(model_monitor):
    # Collect some metrics
    model_monitor.collect_performance_metrics()
    model_monitor.collect_health_metrics()
    
    summary = model_monitor.get_metrics_summary(window_hours=1)
    
    assert 'performance' in summary
    assert 'health' in summary
    assert all(key in summary['performance'] 
              for key in ['avg_latency', 'avg_throughput', 'avg_error_rate'])
    assert all(key in summary['health'] 
              for key in ['avg_memory', 'avg_cpu', 'avg_queue_size'])

def test_alert_checking(model_monitor):
    # Mock metrics that should trigger alerts
    with patch.object(model_monitor, 'get_metrics_summary') as mock_summary:
        mock_summary.return_value = {
            'performance': {
                'avg_latency': 150,  # Above threshold
                'avg_throughput': 100,
                'avg_error_rate': 0.1  # Above threshold
            },
            'health': {
                'avg_memory': 2048,  # Above threshold
                'avg_cpu': 90  # Above threshold
            }
        }
        
        alerts = model_monitor.check_alerts()
        
        assert len(alerts) == 4  # Should have 4 alerts
        assert any('latency' in alert.lower() for alert in alerts)
        assert any('error rate' in alert.lower() for alert in alerts)
        assert any('memory' in alert.lower() for alert in alerts)
        assert any('cpu' in alert.lower() for alert in alerts)

def test_metrics_persistence(model_monitor, tmp_path):
    # Collect metrics
    model_monitor.collect_performance_metrics()
    model_monitor.collect_health_metrics()
    
    # Check file was created
    metrics_file = tmp_path / 'metrics_history.json'
    assert metrics_file.exists()
    
    # Verify content
    with open(metrics_file, 'r') as f:
        saved_metrics = json.load(f)
        assert 'performance' in saved_metrics
        assert 'health' in saved_metrics
        assert len(saved_metrics['performance']) > 0
        assert len(saved_metrics['health']) > 0 