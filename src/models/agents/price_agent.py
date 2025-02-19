import torch
import torch.nn as nn
from typing import Dict, Any
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class PriceAgent(BaseAgent):
    """Agent for suggesting price adjustments."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the price agent.
        
        Args:
            config: Configuration dictionary containing model parameters
        """
        super().__init__(config)
        
        # Define network architecture
        input_size = config['model']['input_size']
        hidden_size = config['model']['hidden_size']
        output_size = config['model']['output_size']
        
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size),
            nn.Tanh()  # Output between -1 and 1 for price adjustments
        )
        
        self.to(self.device)
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass of the model.
        
        Args:
            state: Current market state tensor
            
        Returns:
            Price adjustment suggestions tensor
        """
        return self.network(state)
        
    def get_action(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Get price adjustments for current market state.
        
        Args:
            state: Current market state dictionary
            
        Returns:
            Dictionary of price adjustments for each instrument
        """
        try:
            # Preprocess state
            state_tensor = self.preprocess_state(state)
            
            # Get model predictions
            with torch.no_grad():
                adjustments = self.forward(state_tensor)
                
            # Convert to price adjustments
            max_adjustment = self.config['model']['max_adjustment']
            adjustments = adjustments.cpu().numpy() * max_adjustment
            
            # Create adjustment dictionary
            result = {}
            for i, section in enumerate(state.keys()):
                result[section] = float(adjustments[i])
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting price adjustments: {e}")
            # Return no adjustments on error
            return {section: 0.0 for section in state.keys()} 