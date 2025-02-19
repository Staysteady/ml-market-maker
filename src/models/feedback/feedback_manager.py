import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np

from ...data.storage.database_manager import DatabaseManager
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class FeedbackManager:
    """Manages user feedback and model adjustments."""
    
    def __init__(
        self,
        agent: BaseAgent,
        db_manager: DatabaseManager,
        config: Dict[str, Any]
    ):
        """Initialize feedback manager.
        
        Args:
            agent: The model agent to receive feedback
            db_manager: Database manager for storing feedback
            config: Configuration dictionary
        """
        self.agent = agent
        self.db_manager = db_manager
        self.config = config
        self.feedback_buffer: List[Dict[str, Any]] = []
        
    def record_feedback(
        self,
        instrument_id: str,
        model_adjustment: float,
        user_adjustment: float,
        reason: Optional[str] = None
    ) -> None:
        """Record user feedback on model's price adjustment.
        
        Args:
            instrument_id: Identifier for the instrument
            model_adjustment: Model's suggested adjustment
            user_adjustment: User's actual adjustment
            reason: Optional reason for the adjustment
        """
        try:
            feedback = {
                'timestamp': datetime.now(),
                'instrument_id': instrument_id,
                'model_adjustment': model_adjustment,
                'user_adjustment': user_adjustment,
                'reason': reason
            }
            
            # Store feedback
            self.feedback_buffer.append(feedback)
            
            # Store in database
            self.db_manager.store_user_adjustment(
                instrument_id=instrument_id,
                old_mid=model_adjustment,
                new_mid=user_adjustment,
                reason=reason
            )
            
            # Process feedback if buffer is full
            if len(self.feedback_buffer) >= self.config['feedback']['buffer_size']:
                self._process_feedback_buffer()
                
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            raise
            
    def _process_feedback_buffer(self) -> None:
        """Process accumulated feedback to adjust model behavior."""
        if not self.feedback_buffer:
            return
            
        try:
            # Calculate feedback statistics
            stats = self._calculate_feedback_stats()
            
            # Update model parameters based on feedback
            self._update_model_parameters(stats)
            
            # Clear buffer
            self.feedback_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            raise
            
    def _calculate_feedback_stats(self) -> Dict[str, Any]:
        """Calculate statistics from feedback buffer.
        
        Returns:
            Dictionary of feedback statistics
        """
        stats = {}
        
        # Group feedback by instrument
        by_instrument = {}
        for feedback in self.feedback_buffer:
            inst = feedback['instrument_id']
            if inst not in by_instrument:
                by_instrument[inst] = []
            by_instrument[inst].append(feedback)
            
        # Calculate stats for each instrument
        for inst, feedbacks in by_instrument.items():
            model_adjs = [f['model_adjustment'] for f in feedbacks]
            user_adjs = [f['user_adjustment'] for f in feedbacks]
            
            stats[inst] = {
                'mean_difference': np.mean(
                    np.array(user_adjs) - np.array(model_adjs)
                ),
                'std_difference': np.std(
                    np.array(user_adjs) - np.array(model_adjs)
                ),
                'correlation': np.corrcoef(model_adjs, user_adjs)[0, 1],
                'num_samples': len(feedbacks)
            }
            
        return stats
        
    def _update_model_parameters(self, stats: Dict[str, Any]) -> None:
        """Update model parameters based on feedback statistics.
        
        Args:
            stats: Dictionary of feedback statistics
        """
        # Example adaptation strategy:
        # 1. Adjust learning rate based on prediction accuracy
        # 2. Update max adjustment limits based on user behavior
        # 3. Modify spread constraints based on feedback
        
        try:
            for instrument, inst_stats in stats.items():
                if inst_stats['num_samples'] < self.config['feedback']['min_samples']:
                    continue
                    
                # Adjust max adjustment if model is consistently off
                if abs(inst_stats['mean_difference']) > self.config['feedback']['adjustment_threshold']:
                    current_max = self.agent.config['model']['max_adjustment']
                    new_max = current_max * (1 + inst_stats['mean_difference'])
                    self.agent.config['model']['max_adjustment'] = max(
                        min(new_max, self.config['feedback']['max_adjustment_limit']),
                        self.config['feedback']['min_adjustment_limit']
                    )
                    
                # Adjust spread constraints based on user behavior
                if inst_stats['correlation'] < self.config['feedback']['correlation_threshold']:
                    self.agent.config['training']['spread_weight'] *= 1.2  # Increase spread penalty
                    
        except Exception as e:
            logger.error(f"Error updating model parameters: {e}")
            raise
            
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of current feedback statistics.
        
        Returns:
            Dictionary containing feedback summary
        """
        return self._calculate_feedback_stats() if self.feedback_buffer else {} 