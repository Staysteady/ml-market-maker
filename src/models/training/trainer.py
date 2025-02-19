import logging
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime
import numpy as np
from pathlib import Path

from ..agents.base_agent import BaseAgent
from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(
        self,
        agent: BaseAgent,
        db_manager: DatabaseManager,
        config: Dict[str, Any]
    ):
        """Initialize the trainer.
        
        Args:
            agent: The agent to train
            db_manager: Database manager for getting training data
            config: Training configuration
        """
        self.agent = agent
        self.db_manager = db_manager
        self.config = config
        self.device = agent.device
        
        self.optimizer = optim.Adam(
            agent.parameters(),
            lr=config['training']['learning_rate']
        )
        
        # Loss functions for different components
        self.price_loss = nn.MSELoss()
        self.spread_loss = nn.MSELoss()
        
        # Training metrics history
        self.metrics_history: Dict[str, List[float]] = {
            'total_loss': [],
            'price_loss': [],
            'spread_loss': []
        }
        
    def train_epoch(
        self,
        train_data: List[Dict[str, Any]],
        user_adjustments: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Train for one epoch.
        
        Args:
            train_data: List of market state dictionaries
            user_adjustments: Optional dictionary of user price adjustments
            
        Returns:
            Dictionary of training metrics
        """
        self.agent.train()
        epoch_metrics = {
            'total_loss': 0.0,
            'price_loss': 0.0,
            'spread_loss': 0.0,
            'num_batches': 0
        }
        
        try:
            # Process data in batches
            batch_size = self.config['training']['batch_size']
            for i in range(0, len(train_data), batch_size):
                batch = train_data[i:i + batch_size]
                batch_metrics = self._train_batch(batch, user_adjustments)
                
                # Update epoch metrics
                for k, v in batch_metrics.items():
                    if k != 'num_batches':
                        epoch_metrics[k] += v
                epoch_metrics['num_batches'] += 1
                
            # Average metrics
            for k in epoch_metrics:
                if k != 'num_batches':
                    epoch_metrics[k] /= epoch_metrics['num_batches']
                    
            # Update history
            for k, v in epoch_metrics.items():
                if k != 'num_batches':
                    self.metrics_history[k].append(v)
                    
            return epoch_metrics
            
        except Exception as e:
            logger.error(f"Error in training epoch: {e}")
            raise
            
    def _train_batch(
        self,
        batch: List[Dict[str, Any]],
        user_adjustments: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Train on a single batch.
        
        Args:
            batch: List of market states
            user_adjustments: Optional user adjustments to learn from
            
        Returns:
            Batch training metrics
        """
        self.optimizer.zero_grad()
        
        try:
            # Process each state in batch
            batch_loss = 0.0
            price_loss = 0.0
            spread_loss = 0.0
            
            for state in batch:
                # Get model predictions
                state_tensor = self.agent.preprocess_state(state)
                predictions = self.agent(state_tensor)
                
                # Calculate losses
                if user_adjustments:
                    # Learn from user adjustments
                    target_adjustments = []
                    for section in state.keys():
                        target_adjustments.append(user_adjustments.get(section, 0.0))
                    target_tensor = torch.tensor(
                        target_adjustments,
                        dtype=torch.float32,
                        device=self.device
                    )
                    price_loss += self.price_loss(predictions, target_tensor)
                
                # Add spread maintenance loss
                spread_loss += self._calculate_spread_loss(state, predictions)
                
            # Combine losses
            total_loss = price_loss + self.config['training']['spread_weight'] * spread_loss
            
            # Backpropagate
            total_loss.backward()
            self.optimizer.step()
            
            return {
                'total_loss': total_loss.item(),
                'price_loss': price_loss.item(),
                'spread_loss': spread_loss.item()
            }
            
        except Exception as e:
            logger.error(f"Error in batch training: {e}")
            raise
            
    def _calculate_spread_loss(
        self,
        state: Dict[str, Any],
        predictions: torch.Tensor
    ) -> torch.Tensor:
        """Calculate loss for maintaining reasonable spreads.
        
        Args:
            state: Current market state
            predictions: Model's price adjustment predictions
            
        Returns:
            Spread maintenance loss
        """
        loss = torch.tensor(0.0, device=self.device)
        
        for i, (section, data) in enumerate(state.items()):
            if isinstance(data, dict):  # bid/ask section
                current_spread = torch.mean(
                    torch.tensor(data['ask'].values - data['bid'].values)
                )
                adjustment = predictions[i]
                
                # Penalize if adjustment would make spread too small
                min_spread = self.config['training']['min_spread']
                if current_spread + adjustment < min_spread:
                    loss += (min_spread - (current_spread + adjustment)) ** 2
                    
        return loss
        
    def save_checkpoint(self, path: str) -> None:
        """Save training checkpoint.
        
        Args:
            path: Path to save checkpoint
        """
        checkpoint = {
            'model_state': self.agent.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'metrics_history': self.metrics_history,
            'config': self.config
        }
        
        try:
            torch.save(checkpoint, path)
            logger.info(f"Saved training checkpoint to {path}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise
            
    def load_checkpoint(self, path: str) -> None:
        """Load training checkpoint.
        
        Args:
            path: Path to load checkpoint from
        """
        try:
            checkpoint = torch.load(path, map_location=self.device)
            self.agent.load_state_dict(checkpoint['model_state'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state'])
            self.metrics_history = checkpoint['metrics_history']
            self.config.update(checkpoint['config'])
            logger.info(f"Loaded training checkpoint from {path}")
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            raise 