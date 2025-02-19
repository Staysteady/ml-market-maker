# Getting Started Guide

This guide will help you set up and run the ML pipeline system step by step.

## Prerequisites

1. Install Python 3.8 or higher
2. Install Docker (if you plan to use containerization)
3. Git for version control
4. AWS account (if you plan to use cloud features)

## Initial Setup

1. **Clone the Repository**
   ```bash
   git clone [your-repository-url]
   cd [repository-name]
   ```

2. **Set Up Python Environment**
   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Open .env in your text editor and update the values:
   # - Set your database credentials
   # - Update API configurations
   # - Add your AWS credentials (if using cloud features)
   # - Configure MLflow settings
   ```

## Running the System

You can run the system either directly or using Docker.

### Option 1: Direct Running

1. **Start the API Server**
   ```bash
   # Start the FastAPI server
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Dashboard**
   ```bash
   # In a new terminal window
   streamlit run src.ui.dashboard:main
   ```

3. **Start the Monitoring Service**
   ```bash
   # In a new terminal window
   python -m src.models.monitoring.monitor
   ```

### Option 2: Using Docker

1. **Build the Docker Image**
   ```bash
   docker build -t ml-pipeline .
   ```

2. **Run All Components**
   ```bash
   # Run everything in a single container
   docker run -p 8000:8000 -p 9090:9090 ml-pipeline

   # Or run specific components:
   # API Server
   docker run -e COMPONENT=api -p 8000:8000 ml-pipeline

   # Dashboard
   docker run -e COMPONENT=dashboard -p 8501:8501 ml-pipeline

   # Monitoring
   docker run -e COMPONENT=monitoring -p 9090:9090 ml-pipeline
   ```

## Accessing the System

1. **API Documentation**
   - Open your browser and go to: `http://localhost:8000/docs`
   - This shows the interactive API documentation

2. **Dashboard**
   - Access the dashboard at: `http://localhost:8501`
   - Here you can:
     - Monitor model performance
     - View training progress
     - Check system metrics

3. **Monitoring**
   - Access Prometheus metrics at: `http://localhost:9090`
   - If configured, access Grafana at: `http://localhost:3000`

## Training Your First Model

1. **Prepare Your Data**
   - Place your training data in the appropriate format
   - See `docs/data_format.md` for data requirements

2. **Configure Training Parameters**
   - Edit `config/training_config.yaml` to set:
     - Model architecture
     - Training parameters
     - Data split ratios

3. **Start Training**
   ```bash
   # Using the API
   curl -X POST http://localhost:8000/api/v1/models/train \
     -H "Content-Type: application/json" \
     -d '{
       "model_name": "my_first_model",
       "dataset_path": "path/to/your/data.csv",
       "parameters": {
         "learning_rate": 0.001,
         "batch_size": 32,
         "epochs": 10
       }
     }'
   ```

4. **Monitor Training**
   - Open the dashboard at `http://localhost:8501`
   - Navigate to the "Training" section
   - Watch real-time training progress

## Common Operations

### Checking Model Status
```bash
curl http://localhost:8000/api/v1/models/my_first_model/status
```

### Making Predictions
```bash
curl -X POST http://localhost:8000/api/v1/models/my_first_model/predict \
  -H "Content-Type: application/json" \
  -d '{"data": ["your input data here"]}'
```

### Viewing Model Metrics
```bash
curl http://localhost:8000/api/v1/models/my_first_model/metrics
```

## Troubleshooting

1. **API Not Starting**
   - Check if the port 8000 is already in use
   - Verify environment variables in `.env`
   - Check the logs in `logs/app.log`

2. **Dashboard Not Loading**
   - Ensure Streamlit is installed correctly
   - Check if the API server is running
   - Verify the connection settings

3. **Training Failures**
   - Check the data format
   - Verify GPU availability (if using)
   - Check the training logs

## Getting Help

- Check the documentation in the `docs/` directory
- Review the API documentation at `http://localhost:8000/docs`
- Check the logs in the `logs/` directory
- Refer to specific component documentation:
  - `docs/api.md` for API details
  - `docs/models.md` for model information
  - `docs/configuration.md` for configuration options 