# Configuration Guide

## Environment Variables

### API Configuration
```bash
# API settings
API_HOST=localhost
API_PORT=8000
API_WORKERS=4
DEBUG=False

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Configuration
```bash
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ml_pipeline
DB_USER=user
DB_PASSWORD=password
```

### ML Model Configuration
```bash
# Model settings
MODEL_VERSION=latest
MODEL_REGISTRY_PATH=./model_registry
BATCH_SIZE=32
NUM_WORKERS=4
```

### AWS Configuration
```bash
# AWS credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2
S3_BUCKET_NAME=ml-models-bucket
```

### MLflow Configuration
```bash
# MLflow settings
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=ml_pipeline
```

### Monitoring Configuration
```bash
# Monitoring settings
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Logging Configuration
```bash
# Logging settings
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=./logs/app.log
```

## Configuration Files

### Training Configuration
Location: `config/training_config.yaml`
```yaml
model:
  type: classification
  architecture: neural_network
  parameters:
    hidden_layers: [64, 32]
    activation: relu
    dropout: 0.2

training:
  batch_size: 32
  epochs: 100
  learning_rate: 0.001
  optimizer: adam
  loss_function: cross_entropy

data:
  train_split: 0.7
  validation_split: 0.15
  test_split: 0.15
  shuffle: true
  random_seed: 42
```

### Monitoring Configuration
Location: `config/monitoring_config.yaml`
```yaml
metrics:
  collection_interval: 60
  retention_days: 30

alerts:
  latency_threshold_ms: 100
  error_rate_threshold: 0.01
  drift_threshold: 0.1

endpoints:
  - name: model_prediction
    path: /api/v1/models/{model_id}/predict
    method: POST
    timeout: 5000

dashboards:
  - name: model_performance
    refresh_interval: 300
    panels:
      - latency
      - throughput
      - error_rate
      - drift_detection
```

### Deployment Configuration
Location: `config/deployment_config.yaml`
```yaml
deployment:
  strategy: rolling
  max_surge: 1
  max_unavailable: 0
  timeout: 300

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi

scaling:
  min_replicas: 2
  max_replicas: 10
  target_cpu_utilization: 70
  target_memory_utilization: 80

healthcheck:
  initial_delay: 30
  period: 10
  timeout: 5
  success_threshold: 1
  failure_threshold: 3
```

## Using Configuration Files

### Loading Environment Variables
```python
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Access variables
api_host = os.getenv('API_HOST')
api_port = int(os.getenv('API_PORT'))
```

### Loading YAML Configuration
```python
import yaml

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Load training configuration
training_config = load_config('config/training_config.yaml')

# Access configuration
batch_size = training_config['training']['batch_size']
learning_rate = training_config['training']['learning_rate']
```

## Best Practices

1. **Security**
   - Never commit sensitive information to version control
   - Use environment variables for secrets
   - Rotate secrets regularly
   - Use secure secret management services in production

2. **Configuration Management**
   - Use different configurations for development and production
   - Version control configuration files
   - Document all configuration options
   - Validate configuration values

3. **Deployment**
   - Use configuration management tools
   - Implement proper access controls
   - Back up configurations
   - Monitor configuration changes 