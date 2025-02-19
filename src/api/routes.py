import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from ..models.deployment.deployment_manager import DeploymentManager
from ..models.serving.model_server import ModelServer
from ..models.monitoring.monitor import ModelMonitor
from ..data.storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class MarketState(BaseModel):
    """Market state for prediction requests."""
    instrument_id: str
    bid_prices: List[float]
    ask_prices: List[float]
    timestamp: Optional[datetime] = None

class PredictionResponse(BaseModel):
    """Response for prediction requests."""
    adjustments: Dict[str, float]
    model_version: str
    prediction_id: str
    latency_ms: float

class DeploymentRequest(BaseModel):
    """Request for model deployment."""
    version_id: str
    description: str
    dry_run: Optional[bool] = False

class DeploymentResponse(BaseModel):
    """Response for deployment operations."""
    success: bool
    message: str
    deployment_id: Optional[str] = None

class MetricsResponse(BaseModel):
    """Response for metrics requests."""
    performance: Dict[str, float]
    health: Dict[str, float]
    alerts: List[str]

# Dependency Injection
def get_deployment_manager() -> DeploymentManager:
    """Get deployment manager instance."""
    # This would be properly initialized in your app startup
    pass

def get_model_server() -> ModelServer:
    """Get model server instance."""
    pass

def get_model_monitor() -> ModelMonitor:
    """Get model monitor instance."""
    pass

# API Endpoints
@router.post("/predict", response_model=PredictionResponse)
async def predict(
    market_state: MarketState,
    background_tasks: BackgroundTasks,
    model_server: ModelServer = Depends(get_model_server)
) -> Dict[str, Any]:
    """Get price adjustments for market state."""
    try:
        # Convert to internal format
        state_dict = {
            market_state.instrument_id: {
                'bid': market_state.bid_prices,
                'ask': market_state.ask_prices
            }
        }
        
        # Get prediction
        start_time = datetime.now()
        adjustments = model_server.predict(state_dict)
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate response
        response = {
            'adjustments': adjustments,
            'model_version': model_server.current_model_version,
            'prediction_id': f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'latency_ms': latency
        }
        
        # Store prediction asynchronously
        background_tasks.add_task(
            model_server._store_prediction,
            adjustments,
            state_dict
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_model(
    request: DeploymentRequest,
    deployment_manager: DeploymentManager = Depends(get_deployment_manager)
) -> Dict[str, Any]:
    """Deploy a model version."""
    try:
        success = deployment_manager.deploy_model(
            request.version_id,
            request.description,
            request.dry_run
        )
        
        if success:
            return {
                'success': True,
                'message': 'Deployment successful',
                'deployment_id': f"dep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        else:
            return {
                'success': False,
                'message': 'Deployment failed',
                'deployment_id': None
            }
            
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    steps: int = 1,
    deployment_manager: DeploymentManager = Depends(get_deployment_manager)
) -> Dict[str, Any]:
    """Rollback to previous deployment."""
    try:
        success = deployment_manager.rollback_deployment(steps)
        
        return {
            'success': success,
            'message': 'Rollback successful' if success else 'Rollback failed',
            'deployment_id': None
        }
        
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=Dict[str, Any])
async def get_status(
    deployment_manager: DeploymentManager = Depends(get_deployment_manager)
) -> Dict[str, Any]:
    """Get current deployment status."""
    try:
        return deployment_manager.get_deployment_status()
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    window_hours: int = 24,
    model_monitor: ModelMonitor = Depends(get_model_monitor)
) -> Dict[str, Any]:
    """Get model metrics."""
    try:
        metrics = model_monitor.get_metrics_summary(window_hours)
        alerts = model_monitor.check_alerts()
        
        return {
            'performance': metrics['performance'],
            'health': metrics['health'],
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/versions", response_model=List[Dict[str, Any]])
async def list_versions(
    tags: Optional[List[str]] = None,
    deployment_manager: DeploymentManager = Depends(get_deployment_manager)
) -> List[Dict[str, Any]]:
    """List available model versions."""
    try:
        return deployment_manager.version_manager.list_versions(tags=tags)
    except Exception as e:
        logger.error(f"Version listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 