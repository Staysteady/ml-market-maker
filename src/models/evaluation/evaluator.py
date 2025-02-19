import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import torch

from ..agents.base_agent import BaseAgent
from ...data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Evaluates model performance."""
    
    def __init__(
        self,
        agent: BaseAgent,
        db_manager: DatabaseManager,
        config: Dict[str, Any]
    ):
        """Initialize the evaluator.
        
        Args:
            agent: The agent to evaluate
            db_manager: Database manager for getting evaluation data
            config: Evaluation configuration
        """
        self.agent = agent
        self.db_manager = db_manager
        self.config = config
        
    def evaluate(
        self,
        test_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate model performance.
        
        Args:
            test_data: List of market states to evaluate on
            
        Returns:
            Dictionary of evaluation metrics
        """
        self.agent.eval()
        metrics = {
            'mean_adjustment': 0.0,
            'adjustment_std': 0.0,
            'mean_spread_impact': 0.0,
            'profitable_adjustments': 0.0
        }
        
        try:
            adjustments = []
            spread_impacts = []
            profitable = 0
            
            with torch.no_grad():
                for state in test_data:
                    # Get model's price adjustments
                    state_adjustments = self.agent.get_action(state)
                    
                    # Calculate metrics
                    adj_values = list(state_adjustments.values())
                    adjustments.extend(adj_values)
                    
                    # Calculate spread impact
                    spread_impact = self._calculate_spread_impact(
                        state, state_adjustments)
                    spread_impacts.append(spread_impact)
                    
                    # Check if adjustment would be profitable
                    if self._is_profitable_adjustment(state, state_adjustments):
                        profitable += 1
                        
            # Calculate final metrics
            metrics['mean_adjustment'] = np.mean(adjustments)
            metrics['adjustment_std'] = np.std(adjustments)
            metrics['mean_spread_impact'] = np.mean(spread_impacts)
            metrics['profitable_adjustments'] = profitable / len(test_data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in model evaluation: {e}")
            raise
            
    def _calculate_spread_impact(
        self,
        state: Dict[str, Any],
        adjustments: Dict[str, float]
    ) -> float:
        """Calculate how adjustments affect spreads.
        
        Args:
            state: Current market state
            adjustments: Model's suggested price adjustments
            
        Returns:
            Average spread impact
        """
        impacts = []
        
        for section, data in state.items():
            if isinstance(data, dict):  # bid/ask section
                current_spread = np.mean(data['ask'].values - data['bid'].values)
                new_spread = current_spread + adjustments[section]
                impacts.append(new_spread - current_spread)
                
        return np.mean(impacts) if impacts else 0.0
        
    def _is_profitable_adjustment(
        self,
        state: Dict[str, Any],
        adjustments: Dict[str, float]
    ) -> bool:
        """Check if adjustments would be profitable.
        
        Args:
            state: Current market state
            adjustments: Model's suggested price adjustments
            
        Returns:
            True if adjustments seem profitable
        """
        # Simple profitability check - could be made more sophisticated
        for section, data in state.items():
            if isinstance(data, dict):
                current_spread = np.mean(data['ask'].values - data['bid'].values)
                new_spread = current_spread + adjustments[section]
                
                # Consider profitable if maintains reasonable spread
                min_spread = self.config['evaluation']['min_profitable_spread']
                if new_spread < min_spread:
                    return False
                    
        return True 