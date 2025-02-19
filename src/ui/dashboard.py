import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"

def init_session_state():
    """Initialize session state variables."""
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 30
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def create_metric_chart(history: list, metric_name: str) -> go.Figure:
    """Create a time series chart for a metric."""
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[metric_name],
        mode='lines+markers',
        name=metric_name
    ))
    
    fig.update_layout(
        title=f"{metric_name.replace('_', ' ').title()} Over Time",
        xaxis_title="Time",
        yaxis_title="Value",
        height=300
    )
    
    return fig

def main():
    """Main dashboard application."""
    st.set_page_config(
        page_title="Model Management Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    init_session_state()
    
    # Header
    st.title("Model Management Dashboard")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        refresh_interval = st.slider(
            "Refresh Interval (seconds)",
            min_value=5,
            max_value=300,
            value=st.session_state.refresh_interval
        )
        
        if st.button("Refresh Now"):
            st.session_state.last_refresh = datetime.now()
            
    # Auto-refresh logic
    if (datetime.now() - st.session_state.last_refresh).seconds >= refresh_interval:
        st.session_state.last_refresh = datetime.now()
        st.experimental_rerun()
        
    try:
        # Get current status
        status_response = requests.get(f"{API_BASE_URL}/status")
        status = status_response.json()
        
        # Get metrics
        metrics_response = requests.get(f"{API_BASE_URL}/metrics")
        metrics = metrics_response.json()
        
        # Status Section
        st.header("System Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Model Version",
                status['current_version'],
                help="Currently deployed model version"
            )
            
        with col2:
            health_color = "🟢" if status['health_status'] == 'healthy' else "🔴"
            st.metric(
                "Health Status",
                f"{health_color} {status['health_status'].title()}",
                help="Current system health status"
            )
            
        with col3:
            st.metric(
                "Deployment Time",
                format_timestamp(status['deployment_time']),
                help="Time of last deployment"
            )
            
        # Alerts Section
        if metrics['alerts']:
            st.warning("Active Alerts")
            for alert in metrics['alerts']:
                st.write(f"⚠️ {alert}")
                
        # Performance Metrics
        st.header("Performance Metrics")
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            st.metric(
                "Average Latency",
                f"{metrics['performance']['avg_latency']:.2f}ms",
                help="Average prediction latency"
            )
            st.metric(
                "Error Rate",
                f"{metrics['performance']['avg_error_rate']:.2%}",
                help="Average prediction error rate"
            )
            
        with perf_col2:
            st.metric(
                "Throughput",
                f"{metrics['performance']['avg_throughput']:.1f}/s",
                help="Average predictions per second"
            )
            st.metric(
                "Accuracy",
                f"{metrics['performance']['avg_accuracy']:.2%}",
                help="Average prediction accuracy"
            )
            
        # System Health
        st.header("System Health")
        health_col1, health_col2 = st.columns(2)
        
        with health_col1:
            st.metric(
                "Memory Usage",
                f"{metrics['health']['avg_memory']:.0f}MB",
                help="Average memory usage"
            )
            
        with health_col2:
            st.metric(
                "CPU Usage",
                f"{metrics['health']['avg_cpu']:.1f}%",
                help="Average CPU usage"
            )
            
        # Model Versions
        st.header("Model Versions")
        versions_response = requests.get(f"{API_BASE_URL}/versions")
        versions = versions_response.json()
        
        version_df = pd.DataFrame(versions)
        version_df['timestamp'] = pd.to_datetime(version_df['timestamp'])
        version_df = version_df.sort_values('timestamp', ascending=False)
        
        st.dataframe(
            version_df[['version_id', 'timestamp', 'description', 'tags']],
            use_container_width=True
        )
        
        # Deployment Controls
        st.header("Deployment Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_version = st.selectbox(
                "Select Version",
                version_df['version_id'].tolist()
            )
            deployment_description = st.text_input(
                "Deployment Description",
                placeholder="Enter deployment description"
            )
            
        with col2:
            dry_run = st.checkbox("Dry Run", value=True)
            if st.button("Deploy"):
                if not deployment_description:
                    st.error("Please enter a deployment description")
                else:
                    response = requests.post(
                        f"{API_BASE_URL}/deploy",
                        json={
                            'version_id': selected_version,
                            'description': deployment_description,
                            'dry_run': dry_run
                        }
                    )
                    result = response.json()
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['message'])
                        
            if st.button("Rollback"):
                if st.checkbox("Confirm Rollback"):
                    response = requests.post(f"{API_BASE_URL}/rollback")
                    result = response.json()
                    if result['success']:
                        st.success("Rollback successful")
                    else:
                        st.error("Rollback failed")
                        
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        
if __name__ == "__main__":
    main() 