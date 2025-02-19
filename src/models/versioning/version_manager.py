import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path
import shutil
import hashlib

from ..agents.base_agent import BaseAgent
from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ModelVersionManager:
    """Manages model versions and deployment."""
    
    def __init__(
        self,
        base_dir: str,
        db_manager: DatabaseManager,
        config: Dict[str, Any]
    ):
        """Initialize version manager.
        
        Args:
            base_dir: Base directory for model storage
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        self.base_dir = Path(base_dir)
        self.db_manager = db_manager
        self.config = config
        
        # Create directory structure
        self.models_dir = self.base_dir / 'models'
        self.active_dir = self.base_dir / 'active'
        self.archive_dir = self.base_dir / 'archive'
        
        for directory in [self.models_dir, self.active_dir, self.archive_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Load version history
        self.version_history = self._load_version_history()
        
    def register_model(
        self,
        model: BaseAgent,
        metrics: Dict[str, float],
        description: str,
        tags: Optional[List[str]] = None
    ) -> str:
        """Register a new model version.
        
        Args:
            model: The model to register
            metrics: Model performance metrics
            description: Description of the model version
            tags: Optional tags for the model
            
        Returns:
            Version identifier
        """
        try:
            # Generate version ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_hash = self._compute_model_hash(model)
            version_id = f"v{timestamp}_{model_hash[:8]}"
            
            # Create version directory
            version_dir = self.models_dir / version_id
            version_dir.mkdir()
            
            # Save model and metadata
            model_path = version_dir / 'model.pt'
            model.save(str(model_path))
            
            metadata = {
                'version_id': version_id,
                'timestamp': timestamp,
                'description': description,
                'metrics': metrics,
                'tags': tags or [],
                'config': model.config,
                'hash': model_hash
            }
            
            metadata_path = version_dir / 'metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            # Update version history
            self.version_history[version_id] = metadata
            self._save_version_history()
            
            logger.info(f"Registered new model version: {version_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
            
    def activate_version(self, version_id: str) -> None:
        """Activate a specific model version.
        
        Args:
            version_id: Version identifier to activate
        """
        try:
            version_dir = self.models_dir / version_id
            if not version_dir.exists():
                raise ValueError(f"Version {version_id} not found")
                
            # Archive current active version if exists
            current_active = list(self.active_dir.glob('*'))
            if current_active:
                for item in current_active:
                    archive_path = self.archive_dir / item.name
                    shutil.move(str(item), str(archive_path))
                    
            # Copy new version to active directory
            active_path = self.active_dir / version_id
            shutil.copytree(str(version_dir), str(active_path))
            
            logger.info(f"Activated model version: {version_id}")
            
        except Exception as e:
            logger.error(f"Error activating version: {e}")
            raise
            
    def get_active_version(self) -> Optional[str]:
        """Get currently active model version.
        
        Returns:
            Active version ID or None if no active version
        """
        active_versions = list(self.active_dir.glob('*'))
        return active_versions[0].name if active_versions else None
        
    def get_version_info(self, version_id: str) -> Dict[str, Any]:
        """Get information about a specific version.
        
        Args:
            version_id: Version identifier
            
        Returns:
            Version metadata dictionary
        """
        return self.version_history.get(version_id)
        
    def list_versions(
        self,
        tags: Optional[List[str]] = None,
        metric_threshold: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """List model versions with optional filtering.
        
        Args:
            tags: Optional list of tags to filter by
            metric_threshold: Optional metric thresholds
            
        Returns:
            List of version metadata dictionaries
        """
        versions = list(self.version_history.values())
        
        # Filter by tags
        if tags:
            versions = [
                v for v in versions
                if any(tag in v['tags'] for tag in tags)
            ]
            
        # Filter by metrics
        if metric_threshold:
            versions = [
                v for v in versions
                if all(
                    v['metrics'].get(metric, 0) >= threshold
                    for metric, threshold in metric_threshold.items()
                )
            ]
            
        return sorted(
            versions,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
    def _compute_model_hash(self, model: BaseAgent) -> str:
        """Compute hash of model state for versioning.
        
        Args:
            model: The model to hash
            
        Returns:
            Hash string
        """
        state_dict = model.state_dict()
        state_bytes = json.dumps(
            {k: v.tolist() for k, v in state_dict.items()},
            sort_keys=True
        ).encode()
        return hashlib.sha256(state_bytes).hexdigest()
        
    def _load_version_history(self) -> Dict[str, Dict[str, Any]]:
        """Load version history from disk."""
        history_path = self.base_dir / 'version_history.json'
        if history_path.exists():
            with open(history_path, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_version_history(self) -> None:
        """Save version history to disk."""
        history_path = self.base_dir / 'version_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.version_history, f, indent=2) 