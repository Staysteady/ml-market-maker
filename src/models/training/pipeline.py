import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
from pathlib import Path
import json

from ..agents.base_agent import BaseAgent
from ..agents.price_agent import PriceAgent
from ..feedback.feedback_manager import FeedbackManager
from ..evaluation.evaluator import ModelEvaluator
from .trainer import ModelTrainer
from ...data.capture.data_collector import DataCollector
from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class TrainingPipeline:
    """Orchestrates the model training process."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        db_manager: DatabaseManager,
        checkpoint_dir: Optional[str] = None
    ):
        """Initialize training pipeline.
        
        Args:
            config: Configuration dictionary
            db_manager: Database manager instance
            checkpoint_dir: Optional directory for checkpoints
        """
        self.config = config
        self.db_manager = db_manager
        self.checkpoint_dir = Path(checkpoint_dir or 'checkpoints')
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.agent = self._create_agent()
        self.trainer = ModelTrainer(self.agent, db_manager, config)
        self.evaluator = ModelEvaluator(self.agent, db_manager, config)
        self.feedback_manager = FeedbackManager(self.agent, db_manager, config)
        self.data_collector = DataCollector(db_manager, config)
        
        # Training state
        self.current_epoch = 0
        self.best_metrics: Optional[Dict[str, float]] = None
        
    def _create_agent(self) -> BaseAgent:
        """Create model agent based on configuration."""
        return PriceAgent(self.config)
        
    def train(
        self,
        num_epochs: int,
        save_best: bool = True,
        evaluation_interval: int = 1
    ) -> Dict[str, List[float]]:
        """Run training for specified number of epochs.
        
        Args:
            num_epochs: Number of epochs to train
            save_best: Whether to save best model
            evaluation_interval: Epochs between evaluations
            
        Returns:
            Dictionary of training metrics
        """
        try:
            metrics_history = {
                'train_loss': [],
                'eval_profit': [],
                'eval_spread': []
            }
            
            for epoch in range(num_epochs):
                self.current_epoch = epoch
                logger.info(f"Starting epoch {epoch + 1}/{num_epochs}")
                
                # Get training data
                train_data, user_adjustments = self._get_training_data()
                
                # Train one epoch
                train_metrics = self.trainer.train_epoch(
                    train_data, user_adjustments)
                metrics_history['train_loss'].append(
                    train_metrics['total_loss'])
                
                # Evaluate if needed
                if (epoch + 1) % evaluation_interval == 0:
                    eval_metrics = self._evaluate_model()
                    metrics_history['eval_profit'].append(
                        eval_metrics['profitable_adjustments'])
                    metrics_history['eval_spread'].append(
                        eval_metrics['mean_spread_impact'])
                    
                    # Save if best
                    if save_best and self._is_best_model(eval_metrics):
                        self._save_best_model(eval_metrics)
                        
                # Save checkpoint
                self._save_checkpoint()
                
            return metrics_history
            
        except Exception as e:
            logger.error(f"Error in training pipeline: {e}")
            raise
            
    def _get_training_data(self) -> tuple:
        """Get data for current training epoch."""
        # Calculate time window for training data
        end_time = datetime.now()
        start_time = end_time - timedelta(
            days=self.config['training']['data_window_days'])
            
        return self.data_collector.get_training_data(
            start_time=start_time,
            end_time=end_time
        )
        
    def _evaluate_model(self) -> Dict[str, float]:
        """Evaluate current model performance."""
        # Get evaluation data
        eval_end = datetime.now()
        eval_start = eval_end - timedelta(
            days=self.config['evaluation']['eval_window_days'])
            
        eval_data, _ = self.data_collector.get_training_data(
            start_time=eval_start,
            end_time=eval_end
        )
        
        return self.evaluator.evaluate(eval_data)
        
    def _is_best_model(self, metrics: Dict[str, float]) -> bool:
        """Check if current model is best so far."""
        if self.best_metrics is None:
            return True
            
        # Compare based on profitable adjustments and spread impact
        current_score = (
            metrics['profitable_adjustments'] -
            abs(metrics['mean_spread_impact'])
        )
        best_score = (
            self.best_metrics['profitable_adjustments'] -
            abs(self.best_metrics['mean_spread_impact'])
        )
        
        return current_score > best_score
        
    def _save_best_model(self, metrics: Dict[str, float]) -> None:
        """Save current model as best model."""
        self.best_metrics = metrics
        best_path = self.checkpoint_dir / 'best_model.pt'
        self.agent.save(str(best_path))
        
        # Save metrics
        metrics_path = self.checkpoint_dir / 'best_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)
            
    def _save_checkpoint(self) -> None:
        """Save training checkpoint."""
        checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{self.current_epoch}.pt'
        self.trainer.save_checkpoint(str(checkpoint_path))
        
    def load_best_model(self) -> None:
        """Load the best performing model."""
        best_path = self.checkpoint_dir / 'best_model.pt'
        if best_path.exists():
            self.agent.load(str(best_path))
            
            # Load metrics
            metrics_path = self.checkpoint_dir / 'best_metrics.json'
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    self.best_metrics = json.load(f)
                    
    def resume_from_checkpoint(self, epoch: int) -> None:
        """Resume training from a specific checkpoint.
        
        Args:
            epoch: Epoch number to resume from
        """
        checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pt'
        if checkpoint_path.exists():
            self.trainer.load_checkpoint(str(checkpoint_path))
            self.current_epoch = epoch 