import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
import json
from pathlib import Path

from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for model performance metrics."""
    prediction_latency: float  # Average prediction time in ms
    prediction_throughput: float  # Predictions per second
    error_rate: float  # Percentage of failed predictions
    queue_utilization: float  # Percentage of queue capacity used
    prediction_accuracy: float  # Accuracy of price adjustments
    spread_compliance: float  # Percentage of spreads within limits
    
@dataclass
class HealthMetrics:
    """Container for model health metrics."""
    memory_usage: float  # Memory usage in MB
    cpu_usage: float  # CPU usage percentage
    gpu_usage: Optional[float]  # GPU usage percentage if available
    queue_size: int  # Current prediction queue size
    active_threads: int  # Number of active worker threads
    uptime: float  # Server uptime in hours

class ModelMonitor:
    """Monitors model performance and system health."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict[str, Any],
        metrics_dir: Optional[str] = None
    ):
        """Initialize model monitor.
        
        Args:
            db_manager: Database manager instance
            config: Configuration dictionary
            metrics_dir: Optional directory for metrics storage
        """
        self.db_manager = db_manager
        self.config = config
        self.metrics_dir = Path(metrics_dir or 'metrics')
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics storage
        self.performance_history: List[Dict[str, Any]] = []
        self.health_history: List[Dict[str, Any]] = []
        
        # Load existing metrics if any
        self._load_metrics_history()
        
    def collect_performance_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PerformanceMetrics:
        """Collect model performance metrics.
        
        Args:
            start_time: Optional start time for metrics collection
            end_time: Optional end time for metrics collection
            
        Returns:
            PerformanceMetrics object
        """
        try:
            # Set default time window if not provided
            end_time = end_time or datetime.now()
            start_time = start_time or (end_time - timedelta(
                minutes=self.config['monitoring']['metrics_window_minutes']
            ))
            
            # Get predictions from database
            predictions = self._get_predictions(start_time, end_time)
            
            # Calculate metrics
            metrics = PerformanceMetrics(
                prediction_latency=self._calculate_latency(predictions),
                prediction_throughput=self._calculate_throughput(predictions),
                error_rate=self._calculate_error_rate(predictions),
                queue_utilization=self._calculate_queue_utilization(predictions),
                prediction_accuracy=self._calculate_accuracy(predictions),
                spread_compliance=self._calculate_spread_compliance(predictions)
            )
            
            # Store metrics
            self._store_performance_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            raise
            
    def collect_health_metrics(self) -> HealthMetrics:
        """Collect system health metrics.
        
        Returns:
            HealthMetrics object
        """
        try:
            import psutil
            import torch
            
            # Get system metrics
            process = psutil.Process()
            metrics = HealthMetrics(
                memory_usage=process.memory_info().rss / 1024 / 1024,  # MB
                cpu_usage=process.cpu_percent(),
                gpu_usage=self._get_gpu_usage() if torch.cuda.is_available() else None,
                queue_size=self._get_queue_size(),
                active_threads=threading.active_count(),
                uptime=self._get_uptime()
            )
            
            # Store metrics
            self._store_health_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
            raise
            
    def get_metrics_summary(
        self,
        window_hours: int = 24
    ) -> Dict[str, Dict[str, float]]:
        """Get summary of recent metrics.
        
        Args:
            window_hours: Hours of history to include
            
        Returns:
            Dictionary of metric summaries
        """
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        
        # Filter recent metrics
        recent_performance = [
            m for m in self.performance_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        recent_health = [
            m for m in self.health_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        # Calculate summaries
        return {
            'performance': {
                'avg_latency': np.mean([m['prediction_latency'] for m in recent_performance]),
                'avg_throughput': np.mean([m['prediction_throughput'] for m in recent_performance]),
                'avg_error_rate': np.mean([m['error_rate'] for m in recent_performance]),
                'avg_accuracy': np.mean([m['prediction_accuracy'] for m in recent_performance])
            },
            'health': {
                'avg_memory': np.mean([m['memory_usage'] for m in recent_health]),
                'avg_cpu': np.mean([m['cpu_usage'] for m in recent_health]),
                'avg_queue_size': np.mean([m['queue_size'] for m in recent_health])
            }
        }
        
    def check_alerts(self) -> List[str]:
        """Check for metric alerts based on thresholds.
        
        Returns:
            List of alert messages
        """
        alerts = []
        summary = self.get_metrics_summary(
            window_hours=self.config['monitoring']['alert_window_hours']
        )
        
        # Check performance alerts
        if summary['performance']['avg_latency'] > self.config['monitoring']['max_latency_ms']:
            alerts.append(f"High prediction latency: {summary['performance']['avg_latency']:.2f}ms")
            
        if summary['performance']['avg_error_rate'] > self.config['monitoring']['max_error_rate']:
            alerts.append(f"High error rate: {summary['performance']['avg_error_rate']:.2%}")
            
        # Check health alerts
        if summary['health']['avg_memory'] > self.config['monitoring']['max_memory_mb']:
            alerts.append(f"High memory usage: {summary['health']['avg_memory']:.0f}MB")
            
        if summary['health']['avg_cpu'] > self.config['monitoring']['max_cpu_percent']:
            alerts.append(f"High CPU usage: {summary['health']['avg_cpu']:.1f}%")
            
        return alerts
        
    def _get_predictions(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Get predictions from database."""
        return pd.read_sql_query(
            """
            SELECT * FROM model_predictions
            WHERE timestamp BETWEEN ? AND ?
            """,
            self.db_manager._get_connection(),
            params=[start_time, end_time],
            parse_dates=['timestamp']
        )
        
    def _calculate_latency(self, predictions: pd.DataFrame) -> float:
        """Calculate average prediction latency."""
        return predictions['latency_ms'].mean()
        
    def _calculate_throughput(self, predictions: pd.DataFrame) -> float:
        """Calculate prediction throughput."""
        time_range = (predictions['timestamp'].max() - 
                     predictions['timestamp'].min()).total_seconds()
        return len(predictions) / time_range if time_range > 0 else 0
        
    def _calculate_error_rate(self, predictions: pd.DataFrame) -> float:
        """Calculate prediction error rate."""
        return (predictions['error'].sum() / len(predictions)) if len(predictions) > 0 else 0
        
    def _calculate_queue_utilization(self, predictions: pd.DataFrame) -> float:
        """Calculate queue utilization."""
        return predictions['queue_size'].mean() / self.config['serving']['queue_size']
        
    def _calculate_accuracy(self, predictions: pd.DataFrame) -> float:
        """Calculate prediction accuracy."""
        return predictions['accuracy'].mean()
        
    def _calculate_spread_compliance(self, predictions: pd.DataFrame) -> float:
        """Calculate spread compliance rate."""
        return predictions['spread_compliant'].mean()
        
    def _get_gpu_usage(self) -> float:
        """Get GPU usage if available."""
        return torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
        
    def _get_queue_size(self) -> int:
        """Get current prediction queue size."""
        return self.db_manager.get_queue_size()
        
    def _get_uptime(self) -> float:
        """Get server uptime in hours."""
        return (datetime.now() - self.start_time).total_seconds() / 3600
        
    def _store_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Store performance metrics."""
        metric_dict = {
            'timestamp': datetime.now().isoformat(),
            **metrics.__dict__
        }
        self.performance_history.append(metric_dict)
        self._save_metrics()
        
    def _store_health_metrics(self, metrics: HealthMetrics) -> None:
        """Store health metrics."""
        metric_dict = {
            'timestamp': datetime.now().isoformat(),
            **metrics.__dict__
        }
        self.health_history.append(metric_dict)
        self._save_metrics()
        
    def _save_metrics(self) -> None:
        """Save metrics to disk."""
        metrics = {
            'performance': self.performance_history,
            'health': self.health_history
        }
        with open(self.metrics_dir / 'metrics_history.json', 'w') as f:
            json.dump(metrics, f, indent=2)
            
    def _load_metrics_history(self) -> None:
        """Load metrics history from disk."""
        history_path = self.metrics_dir / 'metrics_history.json'
        if history_path.exists():
            with open(history_path, 'r') as f:
                metrics = json.load(f)
                self.performance_history = metrics['performance']
                self.health_history = metrics['health'] 