import pytest
import torch
import numpy as np
from src.models.training.trainer import ModelTrainer
from src.models.agents.price_agent import PriceAgent
import pandas as pd

@pytest.fixture
def trainer_config():
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
            'min_spread': 0.25
        }
    }

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def trainer(trainer_config, mock_db_manager):
    agent = PriceAgent(trainer_config)
    return ModelTrainer(agent, mock_db_manager, trainer_config)

def test_trainer_initialization(trainer):
    assert isinstance(trainer.agent, PriceAgent)
    assert isinstance(trainer.optimizer, torch.optim.Adam)
    
def test_train_epoch(trainer, test_state):
    # Create some test data
    train_data = [test_state] * 4  # 4 identical states for testing
    
    metrics = trainer.train_epoch(train_data)
    
    assert 'total_loss' in metrics
    assert 'price_loss' in metrics
    assert 'spread_loss' in metrics
    
def test_checkpoint_save_load(trainer, tmp_path):
    save_path = tmp_path / "checkpoint.pt"
    
    # Train a bit
    train_data = [test_state] * 4
    trainer.train_epoch(train_data)
    
    # Save checkpoint
    trainer.save_checkpoint(str(save_path))
    
    # Create new trainer and load checkpoint
    new_trainer = ModelTrainer(
        PriceAgent(trainer_config),
        mock_db_manager,
        trainer_config
    )
    new_trainer.load_checkpoint(str(save_path))
    
    # Compare states
    for p1, p2 in zip(trainer.agent.parameters(),
                      new_trainer.agent.parameters()):
        assert torch.equal(p1, p2) 