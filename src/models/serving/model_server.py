import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
import threading
from queue import Queue
import time

from ..agents.base_agent import BaseAgent
from ..versioning.version_manager import ModelVersionManager
from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ModelServer:
    """Serves model predictions and handles model updates."""
    
    def __init__(
        self,
        version_manager: ModelVersionManager,
        db_manager: DatabaseManager,
        config: Dict[str, Any]
    ):
        """Initialize model server.
        
        Args:
            version_manager: Model version manager
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        self.version_manager = version_manager
        self.db_manager = db_manager
        self.config = config
        
        # Initialize model
        self.current_model: Optional[BaseAgent] = None
        self.model_lock = threading.Lock()
        
        # Prediction queue for async processing
        self.prediction_queue: Queue = Queue(
            maxsize=config['serving']['queue_size']
        )
        
        # Start prediction worker
        self.is_running = True
        self.worker_thread = threading.Thread(
            target=self._prediction_worker,
            daemon=True
        )
        self.worker_thread.start()
        
        # Load active model
        self._load_active_model()
        
    def predict(
        self,
        market_state: Dict[str, Any],
        async_mode: bool = False
    ) -> Optional[Dict[str, float]]:
        """Get price adjustments for current market state.
        
        Args:
            market_state: Current market state dictionary
            async_mode: Whether to process prediction asynchronously
            
        Returns:
            Dictionary of price adjustments or None if async
        """
        if async_mode:
            try:
                self.prediction_queue.put_nowait((market_state, time.time()))
                return None
            except Queue.Full:
                logger.warning("Prediction queue full, dropping request")
                return None
                
        return self._get_prediction(market_state)
        
    def update_model(self, version_id: Optional[str] = None) -> bool:
        """Update to a new model version.
        
        Args:
            version_id: Specific version to load, or latest if None
            
        Returns:
            True if update successful
        """
        try:
            # Get version to load
            if version_id is None:
                version_id = self.version_manager.get_active_version()
                if version_id is None:
                    logger.error("No active model version found")
                    return False
                    
            # Load new model
            with self.model_lock:
                self._load_model_version(version_id)
                
            logger.info(f"Updated to model version: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            return False
            
    def shutdown(self) -> None:
        """Shutdown the model server."""
        self.is_running = False
        self.worker_thread.join()
        
    def _get_prediction(
        self,
        market_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Get synchronous prediction from model.
        
        Args:
            market_state: Current market state
            
        Returns:
            Dictionary of price adjustments
        """
        with self.model_lock:
            if self.current_model is None:
                raise RuntimeError("No model loaded")
            return self.current_model.get_action(market_state)
            
    def _prediction_worker(self) -> None:
        """Worker thread for processing async predictions."""
        while self.is_running:
            try:
                # Get prediction request
                market_state, request_time = self.prediction_queue.get(timeout=1.0)
                
                # Check if request is still valid
                if time.time() - request_time > self.config['serving']['max_delay']:
                    logger.warning("Dropping stale prediction request")
                    continue
                    
                # Get prediction
                prediction = self._get_prediction(market_state)
                
                # Store prediction
                self._store_prediction(prediction, market_state)
                
            except Queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in prediction worker: {e}")
                
    def _store_prediction(
        self,
        prediction: Dict[str, float],
        market_state: Dict[str, Any]
    ) -> None:
        """Store model prediction in database.
        
        Args:
            prediction: Model's price adjustments
            market_state: Input market state
        """
        try:
            self.db_manager.store_prediction(
                prediction=prediction,
                market_state=market_state,
                model_version=self.current_model_version
            )
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            
    def _load_active_model(self) -> None:
        """Load the currently active model version."""
        version_id = self.version_manager.get_active_version()
        if version_id:
            self._load_model_version(version_id)
        else:
            logger.warning("No active model version found")
            
    def _load_model_version(self, version_id: str) -> None:
        """Load a specific model version.
        
        Args:
            version_id: Version identifier to load
        """
        # Get model path
        model_dir = self.version_manager.active_dir / version_id
        model_path = model_dir / 'model.pt'
        
        if not model_path.exists():
            raise ValueError(f"Model file not found: {model_path}")
            
        # Load metadata
        metadata_path = model_dir / 'metadata.json'
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        # Create and load model
        model = self._create_model(metadata['config'])
        model.load(str(model_path))
        
        self.current_model = model
        self.current_model_version = version_id
        
    def _create_model(self, config: Dict[str, Any]) -> BaseAgent:
        """Create model instance from configuration."""
        # This could be made more flexible to support different model types
        from ..agents.price_agent import PriceAgent
        return PriceAgent(config) 