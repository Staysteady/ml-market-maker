# API Documentation

## Overview

The ML Pipeline API provides endpoints for model training, prediction, and management.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Endpoints

### Model Management

#### Train Model
```http
POST /models/train
Content-Type: application/json

{
    "model_name": "string",
    "dataset_path": "string",
    "parameters": {
        "learning_rate": float,
        "batch_size": integer,
        "epochs": integer
    }
}
```

#### Get Model Status
```http
GET /models/{model_id}/status
```

#### Make Prediction
```http
POST /models/{model_id}/predict
Content-Type: application/json

{
    "data": array
}
```

### Model Versioning

#### List Versions
```http
GET /models/{model_name}/versions
```

#### Get Version Details
```http
GET /models/{model_name}/versions/{version_id}
```

### Model Monitoring

#### Get Model Metrics
```http
GET /models/{model_id}/metrics
```

#### Get Model Performance
```http
GET /models/{model_id}/performance
```

### Feedback Management

#### Submit Feedback
```http
POST /feedback
Content-Type: application/json

{
    "model_id": "string",
    "prediction_id": "string",
    "actual_value": "string",
    "feedback_type": "string"
}
```

## Response Formats

### Success Response
```json
{
    "status": "success",
    "data": {
        // Response data
    }
}
```

### Error Response
```json
{
    "status": "error",
    "error": {
        "code": "string",
        "message": "string"
    }
}
```

## Rate Limiting

- 100 requests per minute per IP address
- 1000 requests per hour per API key

## Error Codes

- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

## Examples

### Training a New Model

```python
import requests

url = "http://localhost:8000/api/v1/models/train"
headers = {
    "Authorization": "Bearer your_token",
    "Content-Type": "application/json"
}
data = {
    "model_name": "sentiment_classifier",
    "dataset_path": "data/sentiment_dataset.csv",
    "parameters": {
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 10
    }
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Making Predictions

```python
import requests

url = "http://localhost:8000/api/v1/models/sentiment_classifier/predict"
headers = {
    "Authorization": "Bearer your_token",
    "Content-Type": "application/json"
}
data = {
    "data": ["This product is amazing!", "The service was terrible."]
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
``` 