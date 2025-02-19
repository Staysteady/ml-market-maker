#!/bin/bash
set -e

# Function to wait for a service to be ready
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    
    echo "Waiting for $service to be ready..."
    while ! nc -z "$host" "$port"; do
        sleep 1
    done
    echo "$service is ready!"
}

# Initialize environment
echo "Initializing environment..."

# Create required directories if they don't exist
mkdir -p logs
mkdir -p model_registry

# Wait for required services if specified in environment
if [ ! -z "$DB_HOST" ] && [ ! -z "$DB_PORT" ]; then
    wait_for_service "$DB_HOST" "$DB_PORT" "database"
fi

if [ ! -z "$MLFLOW_TRACKING_URI" ]; then
    wait_for_service "$(echo $MLFLOW_TRACKING_URI | cut -d/ -f3)" "5000" "MLflow"
fi

# Start the application based on the COMPONENT environment variable
case "$COMPONENT" in
    "api")
        echo "Starting API server..."
        exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
        ;;
    "worker")
        echo "Starting Celery worker..."
        exec celery -A src.worker.celery_app worker --loglevel=info
        ;;
    "dashboard")
        echo "Starting dashboard..."
        exec streamlit run src.ui.dashboard:main
        ;;
    "monitoring")
        echo "Starting monitoring service..."
        exec python -m src.models.monitoring.monitor
        ;;
    *)
        echo "Starting all components..."
        # Start monitoring in the background
        python -m src.models.monitoring.monitor &
        # Start the API server
        exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
        ;;
esac 