# Local Setup Guide

This is a simplified guide for running the ML pipeline system locally on your machine.

## Prerequisites

1. Install Python 3.8 or higher
2. Basic knowledge of using terminal/command prompt

## Quick Start Guide

### 1. Initial Setup

```bash
# Create and activate a virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Basic Configuration

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and only set these essential variables:
```bash
# Basic settings (these are the only ones you need to start)
API_HOST=localhost
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO
MODEL_REGISTRY_PATH=./model_registry
```

### 3. Start the System

Open three terminal windows (all in your project directory with virtual environment activated):

**Terminal 1: Start the API Server**
```bash
uvicorn src.api.main:app --host localhost --port 8000 --reload
```

**Terminal 2: Start the Dashboard**
```bash
streamlit run src.ui.dashboard:main
```

**Terminal 3: Start the Monitoring**
```bash
python -m src.models.monitoring.monitor
```

### 4. Access the System

1. **Dashboard** (Main Interface)
   - Open your browser and go to: `http://localhost:8501`
   - This is where you'll spend most of your time
   - You can:
     - Upload and manage datasets
     - Train new models
     - View model performance
     - Make predictions

2. **API Documentation** (Optional)
   - Available at: `http://localhost:8000/docs`
   - Useful if you want to make direct API calls

3. **Monitoring** (Optional)
   - Available at: `http://localhost:9090`
   - Shows system metrics and model performance

## Training Your First Model

### 1. Prepare Your Data
Place your training data in the `data/` directory. Supported formats:
- CSV files
- Excel files (.xlsx)
- JSON files

Example data structure:
```
data/
  └── my_dataset.csv
```

### 2. Train a Model

**Option 1: Using the Dashboard (Recommended)**
1. Open `http://localhost:8501`
2. Click "Train New Model"
3. Upload your dataset
4. Fill in the training parameters
5. Click "Start Training"

**Option 2: Using Python Script**
```python
# example_train.py
from src.models.training.trainer import train_model

train_model(
    dataset_path="data/my_dataset.csv",
    model_name="my_first_model",
    params={
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 10
    }
)
```

### 3. Make Predictions

**Using the Dashboard:**
1. Go to the "Predictions" tab
2. Select your trained model
3. Upload or input your test data
4. Click "Make Prediction"

**Using Python:**
```python
from src.models.serving.predictor import predict

result = predict(
    model_name="my_first_model",
    data=["your input data here"]
)
print(result)
```

## Project Structure
```
your-project/
├── data/                  # Put your datasets here
├── model_registry/        # Trained models are saved here
├── logs/                  # Log files
└── src/                   # Source code
```

## Troubleshooting

### Common Issues

1. **"Port already in use" Error**
   ```bash
   # Find and kill the process using the port
   # On macOS/Linux:
   lsof -i :8000
   kill -9 <PID>
   # On Windows:
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

2. **"Module not found" Error**
   ```bash
   # Make sure you're in the virtual environment
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   # Reinstall requirements
   pip install -r requirements.txt
   ```

3. **Dashboard Not Loading**
   - Make sure the API server is running (Terminal 1)
   - Check `logs/app.log` for errors
   - Try restarting all three terminals

### Checking Logs

```bash
# View the last 100 lines of logs
tail -f logs/app.log
```

## Getting Help

1. Check the logs in `logs/app.log`
2. Look at the example notebooks in `notebooks/` directory
3. Read the API documentation at `http://localhost:8000/docs`
4. Review other documentation in the `docs/` directory 