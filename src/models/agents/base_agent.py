from typing import Dict, Any, List
import numpy as np
import torch
import torch.nn as nn
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC, nn.Module):
    """Base class for all ML agents."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the base agent.
        
        Args:
            config: Configuration dictionary containing model parameters
        """
        super().__init__()
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    @abstractmethod
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass of the model.
        
        Args:
            state: Current market state tensor
            
        Returns:
            Model output tensor
        """
        pass
        
    @abstractmethod
    def get_action(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Get price adjustments for current market state.
        
        Args:
            state: Current market state dictionary
            
        Returns:
            Dictionary of price adjustments for each instrument
        """
        pass
        
    def preprocess_state(self, state: Dict[str, Any]) -> torch.Tensor:
        """Convert market state dictionary to tensor.
        
        Args:
            state: Market state dictionary
            
        Returns:
            Tensor representation of state
        """
        # Extract features from state
        features = []
        
        for section_name, section_data in state.items():
            if isinstance(section_data, dict):  # bid/ask section
                bid = section_data['bid'].values
                ask = section_data['ask'].values
                spread = ask - bid
                mid = (ask + bid) / 2
                features.extend([
                    np.mean(bid),
                    np.mean(ask),
                    np.mean(spread),
                    np.mean(mid),
                    np.std(bid),
                    np.std(ask)
                ])
            else:  # midpoint section
                mid = section_data.values
                features.extend([
                    np.mean(mid),
                    np.std(mid)
                ])
                
        return torch.tensor(features, dtype=torch.float32, device=self.device)
        
    def save(self, path: str) -> None:
        """Save model state.
        
        Args:
            path: Path to save model state
        """
        try:
            torch.save({
                'model_state': self.state_dict(),
                'config': self.config
            }, path)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
            
    def load(self, path: str) -> None:
        """Load model state.
        
        Args:
            path: Path to load model state from
        """
        try:
            checkpoint = torch.load(path, map_location=self.device)
            self.load_state_dict(checkpoint['model_state'])
            self.config.update(checkpoint['config'])
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise 