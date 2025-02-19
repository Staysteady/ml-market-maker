import pytest
from datetime import datetime
import numpy as np
from unittest.mock import MagicMock, patch
from src.models.feedback.feedback_manager import FeedbackManager

@pytest.fixture
def feedback_config():
    return {
        'feedback': {
            'buffer_size': 10,
            'min_samples': 5,
            'adjustment_threshold': 0.1,
            'correlation_threshold': 0.7,
            'max_adjustment_limit': 1.0,
            'min_adjustment_limit': 0.1
        },
        'model': {
            'max_adjustment': 0.5
        },
        'training': {
            'spread_weight': 0.1
        }
    }

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.config = {
        'model': {'max_adjustment': 0.5},
        'training': {'spread_weight': 0.1}
    }
    return agent

@pytest.fixture
def mock_db_manager():
    return MagicMock()

def test_record_feedback(mock_agent, mock_db_manager, feedback_config):
    manager = FeedbackManager(mock_agent, mock_db_manager, feedback_config)
    
    manager.record_feedback(
        instrument_id='section1',
        model_adjustment=0.25,
        user_adjustment=0.30,
        reason='Test feedback'
    )
    
    assert len(manager.feedback_buffer) == 1
    assert manager.feedback_buffer[0]['instrument_id'] == 'section1'
    mock_db_manager.store_user_adjustment.assert_called_once()

def test_process_feedback_buffer(mock_agent, mock_db_manager, feedback_config):
    manager = FeedbackManager(mock_agent, mock_db_manager, feedback_config)
    
    # Add multiple feedback entries
    for i in range(feedback_config['feedback']['buffer_size']):
        manager.record_feedback(
            instrument_id='section1',
            model_adjustment=0.25,
            user_adjustment=0.30
        )
    
    # Buffer should be cleared after processing
    assert len(manager.feedback_buffer) == 0
    
def test_calculate_feedback_stats(mock_agent, mock_db_manager, feedback_config):
    manager = FeedbackManager(mock_agent, mock_db_manager, feedback_config)
    
    # Add test feedback
    manager.record_feedback('section1', 0.25, 0.30)
    manager.record_feedback('section1', 0.35, 0.40)
    
    stats = manager._calculate_feedback_stats()
    
    assert 'section1' in stats
    assert 'mean_difference' in stats['section1']
    assert 'correlation' in stats['section1']
    
def test_update_model_parameters(mock_agent, mock_db_manager, feedback_config):
    manager = FeedbackManager(mock_agent, mock_db_manager, feedback_config)
    
    # Create test statistics
    stats = {
        'section1': {
            'mean_difference': 0.2,
            'std_difference': 0.1,
            'correlation': 0.5,
            'num_samples': 10
        }
    }
    
    manager._update_model_parameters(stats)
    
    # Verify model parameters were updated
    assert mock_agent.config['training']['spread_weight'] > 0.1 