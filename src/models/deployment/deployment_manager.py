import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import yaml

from ..versioning.version_manager import ModelVersionManager
from ..monitoring.monitor import ModelMonitor
from ..serving.model_server import ModelServer
from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DeploymentManager:
    """Manages model deployment and rollback."""
    
    def __init__(
        self,
        version_manager: ModelVersionManager,
        model_server: ModelServer,
        model_monitor: ModelMonitor,
        db_manager: DatabaseManager,
        config: Dict[str, Any]
    ):
        """Initialize deployment manager.
        
        Args:
            version_manager: Model version manager
            model_server: Model serving instance
            model_monitor: Model monitoring instance
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        self.version_manager = version_manager
        self.model_server = model_server
        self.model_monitor = model_monitor
        self.db_manager = db_manager
        self.config = config
        
        # Load deployment history
        self.deployment_dir = Path(config['deployment']['base_dir'])
        self.deployment_dir.mkdir(parents=True, exist_ok=True)
        self.deployment_history = self._load_deployment_history()
        
    def deploy_model(
        self,
        version_id: str,
        description: str,
        dry_run: bool = False
    ) -> bool:
        """Deploy a model version to production.
        
        Args:
            version_id: Version identifier to deploy
            description: Deployment description
            dry_run: Whether to perform a dry run
            
        Returns:
            True if deployment successful
        """
        try:
            # Verify version exists
            if not self._verify_version(version_id):
                return False
                
            # Run pre-deployment checks
            if not self._run_deployment_checks(version_id):
                return False
                
            if dry_run:
                logger.info("Dry run successful, deployment checks passed")
                return True
                
            # Backup current deployment
            self._backup_current_deployment()
            
            # Update model server
            if not self.model_server.update_model(version_id):
                self._restore_backup()
                return False
                
            # Record deployment
            self._record_deployment(version_id, description)
            
            logger.info(f"Successfully deployed model version: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error during deployment: {e}")
            self._restore_backup()
            return False
            
    def rollback_deployment(self, steps: int = 1) -> bool:
        """Rollback to a previous deployment.
        
        Args:
            steps: Number of versions to rollback
            
        Returns:
            True if rollback successful
        """
        try:
            # Get previous version
            if len(self.deployment_history) < steps + 1:
                logger.error("Not enough deployment history for rollback")
                return False
                
            previous_version = self.deployment_history[-1 - steps]
            version_id = previous_version['version_id']
            
            # Backup current deployment
            self._backup_current_deployment()
            
            # Update model server
            if not self.model_server.update_model(version_id):
                self._restore_backup()
                return False
                
            # Record rollback
            self._record_deployment(
                version_id,
                f"Rollback to version {version_id}",
                is_rollback=True
            )
            
            logger.info(f"Successfully rolled back to version: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            self._restore_backup()
            return False
            
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status.
        
        Returns:
            Dictionary containing deployment status
        """
        current_version = self.model_server.current_model_version
        
        # Get metrics for current deployment
        metrics_summary = self.model_monitor.get_metrics_summary(
            window_hours=self.config['deployment']['status_window_hours']
        )
        
        # Get active alerts
        alerts = self.model_monitor.check_alerts()
        
        return {
            'current_version': current_version,
            'deployment_time': self._get_deployment_time(current_version),
            'metrics': metrics_summary,
            'alerts': alerts,
            'health_status': 'degraded' if alerts else 'healthy'
        }
        
    def _verify_version(self, version_id: str) -> bool:
        """Verify version exists and is valid."""
        version_info = self.version_manager.get_version_info(version_id)
        if not version_info:
            logger.error(f"Version {version_id} not found")
            return False
            
        # Check version meets minimum requirements
        metrics = version_info['metrics']
        requirements = self.config['deployment']['requirements']
        
        for metric, threshold in requirements.items():
            if metrics.get(metric, 0) < threshold:
                logger.error(
                    f"Version {version_id} does not meet {metric} requirement: "
                    f"{metrics.get(metric, 0)} < {threshold}"
                )
                return False
                
        return True
        
    def _run_deployment_checks(self, version_id: str) -> bool:
        """Run pre-deployment validation checks."""
        try:
            # Load and validate model
            model_path = self.version_manager.models_dir / version_id / 'model.pt'
            if not self._validate_model(model_path):
                return False
                
            # Check system resources
            if not self._check_resources():
                return False
                
            # Run integration tests
            if not self._run_integration_tests(version_id):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Deployment check failed: {e}")
            return False
            
    def _validate_model(self, model_path: Path) -> bool:
        """Validate model file integrity and compatibility."""
        try:
            import torch
            # Try loading model
            model = torch.load(model_path, map_location='cpu')
            return True
        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False
            
    def _check_resources(self) -> bool:
        """Check system has required resources."""
        try:
            import psutil
            
            # Check memory
            memory = psutil.virtual_memory()
            if memory.available < self.config['deployment']['min_memory_mb'] * 1024 * 1024:
                logger.error("Insufficient memory available")
                return False
                
            # Check CPU
            if psutil.cpu_percent(interval=1) > self.config['deployment']['max_cpu_percent']:
                logger.error("CPU usage too high")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return False
            
    def _run_integration_tests(self, version_id: str) -> bool:
        """Run integration tests for new version."""
        try:
            # Run pytest with deployment tests
            result = subprocess.run(
                ['pytest', 'tests/integration'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Integration tests failed: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Integration test run failed: {e}")
            return False
            
    def _backup_current_deployment(self) -> None:
        """Backup current deployment state."""
        current_version = self.model_server.current_model_version
        if current_version:
            backup_dir = self.deployment_dir / 'backups' / current_version
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy model and config
            shutil.copy2(
                self.version_manager.active_dir / current_version / 'model.pt',
                backup_dir / 'model.pt'
            )
            shutil.copy2(
                self.version_manager.active_dir / current_version / 'metadata.json',
                backup_dir / 'metadata.json'
            )
            
    def _restore_backup(self) -> None:
        """Restore from most recent backup."""
        backup_dir = self.deployment_dir / 'backups'
        if not backup_dir.exists():
            return
            
        # Get most recent backup
        backups = sorted(backup_dir.iterdir(), key=lambda x: x.stat().st_mtime)
        if not backups:
            return
            
        latest_backup = backups[-1]
        version_id = latest_backup.name
        
        try:
            self.model_server.update_model(version_id)
            logger.info(f"Restored backup version: {version_id}")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            
    def _record_deployment(
        self,
        version_id: str,
        description: str,
        is_rollback: bool = False
    ) -> None:
        """Record deployment in history."""
        deployment = {
            'version_id': version_id,
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'is_rollback': is_rollback
        }
        
        self.deployment_history.append(deployment)
        self._save_deployment_history()
        
    def _load_deployment_history(self) -> List[Dict[str, Any]]:
        """Load deployment history from disk."""
        history_path = self.deployment_dir / 'deployment_history.json'
        if history_path.exists():
            with open(history_path, 'r') as f:
                return json.load(f)
        return []
        
    def _save_deployment_history(self) -> None:
        """Save deployment history to disk."""
        history_path = self.deployment_dir / 'deployment_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.deployment_history, f, indent=2)
            
    def _get_deployment_time(self, version_id: str) -> Optional[str]:
        """Get deployment time for a version."""
        for deployment in reversed(self.deployment_history):
            if deployment['version_id'] == version_id:
                return deployment['timestamp']
        return None 