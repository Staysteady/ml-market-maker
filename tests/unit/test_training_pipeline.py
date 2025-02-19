import pytest
from datetime import datetime
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path
import json

from src.models.training.pipeline import TrainingPipeline

@pytest.fixture
def pipeline_config():
    return {
        'model': {
            'input_size': 24,
            'hidden_size': 64,
            'output_size': 4,
            'max_adjustment': 0.5
        },
        'training': {
            'learning_rate': 0.001,
            'batch_size': 32,
            'spread_weight': 0.1,
            'data_window_days': 7
        },
        'evaluation': {
            'eval_window_days': 1,
            'min_profitable_spread': 0.25
        },
        'feedback': {
            'buffer_size': 10,
            'min_samples': 5
        }
    }

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def pipeline(pipeline_config, mock_db_manager, tmp_path):
    return TrainingPipeline(
        pipeline_config,
        mock_db_manager,
        checkpoint_dir=str(tmp_path)
    )

def test_pipeline_initialization(pipeline):
    assert pipeline.agent is not None
    assert pipeline.trainer is not None
    assert pipeline.evaluator is not None
    assert pipeline.feedback_manager is not None
    assert pipeline.data_collector is not None

def test_training_loop(pipeline, mock_db_manager):
    # Mock training data
    mock_data = ([{'section1': {'bid': np.array([100.25]),
                               'ask': np.array([100.50])}}], {})
    pipeline.data_collector.get_training_data.return_value = mock_data
    
    # Mock evaluation metrics
    mock_metrics = {
        'profitable_adjustments': 0.8,
        'mean_spread_impact': 0.1
    }
    pipeline.evaluator.evaluate.return_value = mock_metrics
    
    # Run training
    metrics = pipeline.train(num_epochs=2)
    
    assert 'train_loss' in metrics
    assert 'eval_profit' in metrics
    assert len(metrics['train_loss']) == 2

def test_model_saving(pipeline, tmp_path):
    # Create mock metrics
    mock_metrics = {
        'profitable_adjustments': 0.8,
        'mean_spread_impact': 0.1
    }
    
    # Save best model
    pipeline._save_best_model(mock_metrics)
    
    # Check files exist
    assert (tmp_path / 'best_model.pt').exists()
    assert (tmp_path / 'best_metrics.json').exists()
    
    # Verify metrics were saved correctly
    with open(tmp_path / 'best_metrics.json', 'r') as f:
        saved_metrics = json.load(f)
    assert saved_metrics == mock_metrics

def test_checkpoint_loading(pipeline, tmp_path):
    # Create and save a checkpoint
    pipeline.current_epoch = 5
    pipeline._save_checkpoint()
    
    # Create new pipeline and load checkpoint
    new_pipeline = TrainingPipeline(
        pipeline_config,
        mock_db_manager,
        checkpoint_dir=str(tmp_path)
    )
    new_pipeline.resume_from_checkpoint(5)
    
    assert new_pipeline.current_epoch == 5 