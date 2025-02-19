import pytest
import torch
import numpy as np
from src.models.agents.price_agent import PriceAgent
import pandas as pd

@pytest.fixture
def model_config():
    return {
        'model': {
            'input_size': 24,  # 6 features per section * 4 sections
            'hidden_size': 64,
            'output_size': 4,  # One adjustment per section
            'max_adjustment': 0.5
        }
    }

@pytest.fixture
def test_state():
    return {
        'section1': {
            'bid': pd.Series([100.25, 100.50]),
            'ask': pd.Series([100.50, 100.75])
        },
        'section2': {
            'bid': pd.Series([50.25, 50.50]),
            'ask': pd.Series([50.50, 50.75])
        }
    }

def test_price_agent_initialization(model_config):
    agent = PriceAgent(model_config)
    assert isinstance(agent, PriceAgent)
    
def test_state_preprocessing(model_config, test_state):
    agent = PriceAgent(model_config)
    state_tensor = agent.preprocess_state(test_state)
    
    assert isinstance(state_tensor, torch.Tensor)
    assert state_tensor.device == agent.device
    
def test_get_action(model_config, test_state):
    agent = PriceAgent(model_config)
    adjustments = agent.get_action(test_state)
    
    assert isinstance(adjustments, dict)
    assert all(isinstance(v, float) for v in adjustments.values())
    assert all(abs(v) <= model_config['model']['max_adjustment'] 
               for v in adjustments.values())
    
def test_model_save_load(model_config, tmp_path):
    agent = PriceAgent(model_config)
    save_path = tmp_path / "test_model.pt"
    
    # Save model
    agent.save(str(save_path))
    
    # Load model
    new_agent = PriceAgent(model_config)
    new_agent.load(str(save_path))
    
    # Compare model parameters
    for p1, p2 in zip(agent.parameters(), new_agent.parameters()):
        assert torch.equal(p1, p2) 